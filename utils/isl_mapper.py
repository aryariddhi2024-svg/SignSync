from utils.dataset_loader import ISL_DATASET

def map_to_isl(tokens: list[str], show_fingerspell: bool = True):
    """
    Maps each token to an ISL image path.

    Returns:
      mapped  : list of (token, image_path) tuples for found words
      missing : list of tokens that could not be mapped at all
    """
    mapped = []
    missing = []

    for token in tokens:
        token_lower = token.lower().strip()

        # 1. Direct match in dataset
        if token_lower in ISL_DATASET:
            mapped.append((token_lower, ISL_DATASET[token_lower]))
            print(f"[isl_mapper] FOUND: '{token_lower}' -> {ISL_DATASET[token_lower]}")

        # 2. Fingerspell letter by letter
        elif show_fingerspell:
            letter_paths = []
            for char in token_lower:
                if char.isalpha() and char in ISL_DATASET:
                    letter_paths.append((char, ISL_DATASET[char]))
            if letter_paths:
                mapped.extend(letter_paths)
                print(f"[isl_mapper] FINGERSPELL: '{token_lower}' -> {[p for _,p in letter_paths]}")
            else:
                missing.append(token_lower)
                print(f"[isl_mapper] MISSING: '{token_lower}'")
        else:
            missing.append(token_lower)
            print(f"[isl_mapper] MISSING (fingerspell off): '{token_lower}'")

    print(f"[isl_mapper] Total mapped: {len(mapped)}, missing: {len(missing)}")
    return mapped, missing
