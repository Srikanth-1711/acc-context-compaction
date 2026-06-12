def dedup(lines: list[str]) -> list[str]:
    """
    Removes consecutive duplicate lines, replacing them with a single line indicating the repeat count.
    """
    if not lines:
        return []

    out = []
    last = None
    count = 0

    for line in lines:
        if line == last:
            count += 1
        else:
            if last is not None:
                if count > 1:
                    out.append(f"{last} (repeated {count} times)")
                else:
                    out.append(last)
            last = line
            count = 1

    if last is not None:
        if count > 1:
            out.append(f"{last} (repeated {count} times)")
        else:
            out.append(last)

    return out
