from fastembed import TextEmbedding

for item in TextEmbedding.list_supported_models():
    print(f"model = {item.get('model')}\nsize = {item.get('size_in_GB')}")
