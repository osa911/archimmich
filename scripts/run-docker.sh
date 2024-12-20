rm -rf dist build;
docker build -t archimmich-builder .;
docker run --rm -v $(pwd):/app archimmich-builder;