import sys

def main():
    with open(sys.argv[1]) as f:
        grid = f.read().splitlines()

    generations = int(sys.argv[2])
    h = len(grid)
    w = len(grid[0]) if h else 0

    alive = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == '#'
    }

    for _ in range(generations):
        count = {}

        for r, c in alive:
            for dr in (-1, 0, 1):
                nr = r + dr
                if nr < 0 or nr >= h:
                    continue
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nc = c + dc
                    if nc < 0 or nc >= w:
                        continue
                    count[(nr, nc)] = count.get((nr, nc), 0) + 1

        new_alive = set()
        for cell, n in count.items():
            if n == 3 or (cell in alive and n == 2):
                new_alive.add(cell)

        alive = new_alive

    output = "\n".join(
        "".join("#" if (r, c) in alive else "." for c in range(w))
        for r in range(h)
    )

    sys.stdout.write(output)

if __name__ == "__main__":
    main()
