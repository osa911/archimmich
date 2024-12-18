pyinstaller \
  --onedir \
  --windowed \
  --optimize "2" \
  --icon=../favicon-180.png \
  --add-data "resources/*:resources" \
  --distpath "dist" \
  --name "Archimmich" \
  archimmich.py;