# The Moon Is a Kite

Entry for make.fun `coolest-art-01` (v2): a small child on a dark hill
flies the full moon as a kite, holding its golden string.

## How it works

`main.py` (Python 3.13, standard library only) draws the picture
procedurally into an RGB buffer — deep navy night sky with stars, one
giant cratered moon, a golden kite string on a bezier curve, layered
dark hills, and a tiny child in a pale coat with a red scarf — then
writes it out as a PNG with a minimal hand-rolled encoder (`zlib` +
`struct`, no image libraries).

It is fully deterministic: a fixed random seed, no clock, no network.
Running it twice writes byte-identical output.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png (1024x1024, ~13 KB)
```

## License

MIT — see `LICENSE`.
