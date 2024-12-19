pyinstaller \
  --onedir \
  --windowed \
  --optimize "2" \
  --icon="src/resources/favicon-180.png" \
  --add-data "src/resources/*:src/resources" \
  --distpath "dist" \
  --paths="src" \
  --name "ArchImmich" \
  src/main.py;