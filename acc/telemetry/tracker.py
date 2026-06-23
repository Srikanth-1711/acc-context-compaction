import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlmodel import create_engine, Session, SQLModel, select, func

from acc.telemetry.models import RunLog

def get_engine():
    db_path = Path.home() / ".acc" / "acc_telemetry.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_url = f"sqlite:///{db_path}"
    return create_engine(sqlite_url)

class AnalyticsTracker:
    def __init__(self):
        self.engine = get_engine()
        SQLModel.metadata.create_all(self.engine)

    def log_run(
        self,
        command: str,
        raw_tokens: int,
        output_tokens: int,
        deduped: bool = False,
        session_id: str = None,
        memories_used: int = 0,
        latency_ms: int = None
    ):
        """Log a command run into the telemetry database."""
        ratio = output_tokens / raw_tokens if raw_tokens > 0 else 1.0
        
        try:
            with Session(self.engine) as session:
                log = RunLog(
                    command=command,
                    raw_tokens=raw_tokens,
                    output_tokens=output_tokens,
                    deduped=deduped,
                    compression_ratio=ratio,
                    session_id=session_id,
                    memories_used=memories_used,
                    latency_ms=latency_ms
                )
                session.add(log)
                session.commit()
        except Exception:
            # Swallow telemetry errors to avoid breaking the core flow
            pass

    def get_json(self, period: str = "all") -> Dict[str, Any]:
        """Get JSON analytics for a period (day, week, month, all)."""
        now = datetime.utcnow()
        if period == "day":
            start_date = now - timedelta(days=1)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = datetime.min

        try:
            with Session(self.engine) as session:
                stmt = select(
                    func.count(RunLog.id).label("total_runs"),
                    func.sum(RunLog.raw_tokens).label("total_raw"),
                    func.sum(RunLog.output_tokens).label("total_output"),
                    func.sum(RunLog.memories_used).label("total_memories")
                ).where(RunLog.timestamp >= start_date)
                
                result = session.exec(stmt).first()
                if not result or result[0] == 0:
                    return {"runs": 0, "saved_tokens": 0, "reduction_pct": 0.0}

                total_runs, total_raw, total_output, total_memories = result
                total_raw = total_raw or 0
                total_output = total_output or 0
                saved = total_raw - total_output
                pct = (saved / total_raw * 100) if total_raw > 0 else 0.0

                return {
                    "period": period,
                    "runs": total_runs,
                    "raw_tokens": total_raw,
                    "output_tokens": total_output,
                    "saved_tokens": saved,
                    "reduction_pct": round(pct, 2),
                    "memories_used": total_memories or 0
                }
        except Exception:
            return {"error": "Failed to fetch analytics"}

    def get_markdown_report(self) -> str:
        """Returns a markdown summary of token savings."""
        data_day = self.get_json("day")
        data_week = self.get_json("week")
        data_month = self.get_json("month")
        data_all = self.get_json("all")
        
        md = "# ACC Telemetry Analytics\n\n"
        md += "| Period | Runs | Raw Tokens | Output Tokens | Saved Tokens | Reduction % | Memories Used |\n"
        md += "|---|---|---|---|---|---|---|\n"
        
        for d in [data_day, data_week, data_month, data_all]:
            if "error" in d:
                continue
            md += f"| {d['period'].capitalize()} | {d['runs']} | {d['raw_tokens']:,} | {d['output_tokens']:,} | {d['saved_tokens']:,} | {d['reduction_pct']}% | {d['memories_used']} |\n"
            
        return md
