#!/usr/bin/env bash
# Install WhiteSur icon theme (default + dark variants) from a source checkout.
# Mirrors the layout produced by the upstream install.sh, without prompts.
# Usage: install-whitesur-icons.sh SRC_DIR DEST_DIR
set -euo pipefail
SRC="$1"
DEST="$2"
NAME=WhiteSur

base="$DEST/$NAME"
dark="$DEST/$NAME-dark"
rm -rf "$base" "$dark"
mkdir -p "$base/status" "$dark"/{apps,categories,emblems,devices,mimes,places,status}

# ---- default (light) variant
cp "$SRC/src/index.theme" "$base/"
cp -r "$SRC"/src/{actions,animations,apps,categories,devices,emotes,emblems,mimes,places,preferences} "$base/"
cp -r "$SRC"/src/status/{16,22,24,32,symbolic} "$base/status/"
rm -f "$base"/places/scalable/user-trash{,-full}-dark.svg
cp -r "$SRC"/links/{actions,apps,categories,devices,emotes,emblems,mimes,places,status,preferences} "$base/"

# ---- dark variant
cp "$SRC/src/index.theme" "$dark/"
sed -i "s/$NAME/$NAME-dark/g" "$dark/index.theme"
cp -r "$SRC/src/actions" "$dark/"
cp -r "$SRC"/src/apps/{16,22,32,symbolic} "$dark/apps/"
cp -r "$SRC"/src/categories/{22,symbolic} "$dark/categories/"
cp -r "$SRC/src/emblems/symbolic" "$dark/emblems/"
cp -r "$SRC/src/mimes/symbolic" "$dark/mimes/"
cp -r "$SRC"/src/devices/{16,22,24,32,symbolic} "$dark/devices/"
cp -r "$SRC"/src/places/{16,22,24,scalable,symbolic} "$dark/places/"
cp -r "$SRC/src/status/symbolic" "$dark/status/"
mv -f "$dark/places/scalable/user-trash-dark.svg" "$dark/places/scalable/user-trash.svg"
mv -f "$dark/places/scalable/user-trash-full-dark.svg" "$dark/places/scalable/user-trash-full.svg"
sed -i "s/#363636/#dedede/g" "$dark"/{actions,devices,places}/{16,22,24}/*.svg \
    "$dark"/apps/{16,22,32}/*.svg "$dark"/categories/22/*.svg "$dark"/{actions,devices}/32/*.svg \
    "$dark"/{actions,apps,categories,emblems,devices,mimes,places,status}/symbolic/*.svg
cp -r "$SRC"/links/actions/{16,22,24,32,symbolic} "$dark/actions/"
cp -r "$SRC"/links/devices/{16,22,24,32,symbolic} "$dark/devices/"
cp -r "$SRC"/links/places/{16,22,24,scalable,symbolic} "$dark/places/"
cp -r "$SRC"/links/apps/{16,22,32,symbolic} "$dark/apps/"
cp -r "$SRC"/links/categories/{22,symbolic} "$dark/categories/"
cp -r "$SRC/links/emblems/symbolic" "$dark/emblems/"
cp -r "$SRC/links/mimes/symbolic" "$dark/mimes/"
cp -r "$SRC/links/status/symbolic" "$dark/status/"
(
    cd "$DEST"
    for d in animations emotes preferences; do ln -sfn "../$NAME/$d" "$NAME-dark/$d"; done
    for d in categories/32 emblems/16 emblems/22 emblems/24 mimes/16 mimes/22 mimes/scalable \
             apps/scalable devices/scalable status/16 status/22 status/24 status/32; do
        ln -sfn "../../$NAME/$d" "$NAME-dark/$d"
    done
)

# ---- light variant: dark status icons for light panels (menu bar in Light mode)
light="$DEST/$NAME-light"
rm -rf "$light"
mkdir -p "$light/status"
cp "$SRC/src/index.theme" "$light/"
sed -i "s/$NAME/$NAME-light/g" "$light/index.theme"
cp -r "$SRC"/src/status/{16,22,24,32} "$light/status/"
sed -i "s/#f2f2f2/#363636/g" "$light"/status/{16,22,24,32}/*
cp -r "$SRC"/links/status/{16,22,24,32} "$light/status/"
(
    cd "$DEST"
    for d in actions animations apps categories devices emotes emblems mimes places preferences; do
        ln -sfn "../$NAME/$d" "$NAME-light/$d"
    done
    ln -sfn "../../$NAME/status/symbolic" "$NAME-light/status/symbolic"
)

for t in "$base" "$dark" "$light"; do
    (
        cd "$t"
        for d in actions animations apps categories devices emotes emblems mimes places preferences status; do
            ln -sfn "$d" "$d@2x"
        done
    )
done
echo "Installed $base, $dark and $light"
