from db import init_db

def main():
    print("Initializing database...")
    init_db()

    print("Indexing process completed successfully!")


if __name__ == '__main__':
    main()
