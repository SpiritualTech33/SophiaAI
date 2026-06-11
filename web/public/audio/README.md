# Cosmic ambient audio

The floating music orb (`web/components/cosmic/CosmicPlayer.tsx`) plays the
files listed in its `TRACKS` array. By default it expects:

- `cosmic-ambient.mp3` — a looping relaxing space/ambient bed.

## How to add or change the music

1. Drop one or more `.mp3` files into this folder (`web/public/audio/`).
2. List them in `TRACKS` inside `CosmicPlayer.tsx`:
   ```ts
   const TRACKS = [
     { src: "/audio/cosmic-ambient.mp3", title: "Cosmic Drift" },
   ];
   ```

## Licensing

Use only audio you have the right to host: your own work, public-domain (CC0),
or royalty-free tracks that permit redistribution. Good sources for free
cosmic/ambient music:

- Pixabay Music (https://pixabay.com/music/) — royalty-free, no attribution.
- Free Music Archive (https://freemusicarchive.org/) — check each track's license.
- Internet Archive (https://archive.org/) — many public-domain works.

If a track requires attribution (e.g. CC-BY), add the credit here and in the
app's footer/credits.
