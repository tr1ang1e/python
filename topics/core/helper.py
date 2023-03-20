def get_bases(ent, tab=0):
    for base in ent.__bases__:
        print(f"{' ' * tab}{base}")
        get_bases(base, tab + 2)
