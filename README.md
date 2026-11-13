# The Last Flag on Kepler Ridge

Entry for make.fun `coolest-art-01`: a lone astronaut plants a flag on an
alien ridge beneath a giant ringed planet.

## How it works

`main.py` (Python 3.13, standard library only) draws the picture
procedurally into an RGB buffer — gradient dusk sky, stars, a small moon,
a banded ringed planet with a day-side terminator, layered mountain
ridges, and a lone astronaut with a glowing visor planting an orange
flag — then writes it out as a PNG with a minimal hand-rolled encoder
(`zlib` + `struct`, no image libraries).

It is fully deterministic: a fixed random seed, no clock, no network.
Running it twice writes byte-identical output.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (1024x1024, ~100 KB)
```

## License

MIT — see `LICENSE`.
