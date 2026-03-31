# Tämä on opetus/demo, joka näyttää miten salasana + salt + pepper + hash toimii.
import os           # os tarvitaan ympäristömuuttujan lukemiseen (PEPPER)
import secrets      # secrets tarvitaan turvalliseen saltin generointiin
import hashlib      # hashlib tarvitaan PBKDF2-HMAC-SHA256 hashin laskentaan. Password-Based Key Derivation Function 2
import base64       # base64 tarvitaan binääridatan esittämiseen luettavassa muodossa (salt ja hash)
import hmac         # hmac tarvitaan turvalliseen hashien vertailuun (compare_digest)

# DEMO-asetukset
ITERATIONS = 200_000
DKLEN = 32

# PEPPER: sovelluksen yhteinen salaisuus (EI tietokantaan).
# Tuotannossa: aina ympäristömuuttujasta / Key Vaultista.
PEPPER = os.environ.get("PASSWORD_PEPPER", "DEMO-PEPPER-CHANGE-ME")

def b64(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")

def show(label: str, value, warning: str = ""):
    """Yksi rivi tulostusta, optional varoitustekstillä."""
    w = f"  [{warning}]" if warning else ""
    print(f"{label:<38}: {value}{w}")

def pbkdf2_hash_show_all_steps(password: str, salt: bytes, pepper: str) -> bytes:
    """
    Näyttää KAIKKI välivaiheet:
      1) password -> bytes
      2) pepper -> bytes
      3) data = password_bytes + pepper_bytes
      4) PBKDF2 käyttää: (data + salt + iterations) => hash
    """
    print("\n--- Hashauksen välivaiheet (näytetään kaikki) ---")

    # 1) Salasana bytes
    password_bytes = password.encode("utf-8")
    show("password (merkkijono)", password, "MASKATTAVA / EI SAA NÄYTTÄÄ")
    show("password_bytes", repr(password_bytes), "EI SAA NÄYTTÄÄ")

    # 2) Pepper bytes
    pepper_bytes = pepper.encode("utf-8")
    show("pepper (merkkijono)", pepper, "EI SAA NÄYTTÄÄ")
    show("pepper_bytes", repr(pepper_bytes), "EI SAA NÄYTTÄÄ")

    # 3) Yhdistetty data (pwd + pepper)
    data = password_bytes + pepper_bytes
    show("data = password_bytes + pepper_bytes", repr(data), "EI SAA NÄYTTÄÄ")

    # 4) Salt (näytetään erikseen, koska se on oma syöte PBKDF2:lle)
    #    (Salt ei liity dataan liittämällä tässä, vaan annetaan PBKDF2:lle erillisenä parametrina.)
    show("salt (raaka bytes)", repr(salt), "tallennetaan (ei lokiin tuotannossa)")
    show("salt (hex)", salt.hex(), "tallennetaan")
    show("salt (base64)", b64(salt), "tallennetaan")

    # 5) PBKDF2 parametrit
    show("PBKDF2 hash_name", "sha256")
    show("PBKDF2 iterations", ITERATIONS)
    show("PBKDF2 dklen", DKLEN)

    # 6) Varsinainen hash-laskenta
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        data,     # password+pepper (bytes)
        salt,     # salt erillisenä
        ITERATIONS,
        dklen=DKLEN
    )

    # 7) Hash ulos
    show("hashed (bytes)", repr(hashed), "tallennetaan")
    show("hashed (hex)", hashed.hex(), "tallennetaan")
    show("hashed (base64)", b64(hashed), "tallennetaan")

    return hashed

def main():
    # "Tietokanta" demon ajaksi muistiin:
    # username -> (salt_bytes, hash_bytes)
    db = {}

    print("=== SALASANA + SALT + PEPPER + HASH (DEMO, kaikki välivaiheet näkyy) ===")
    print("VAROITUS: Tämä demo tulostaa arkaluonteisia arvoja (EI SAA TUOTANNOSSA).")
    if PEPPER == "DEMO-PEPPER-CHANGE-ME":
        print("HUOM: Käytössä demo-pepper. Aseta PASSWORD_PEPPER ympäristömuuttujaan oikeassa käytössä.")

    while True:
        print("\nValitse toiminto:")
        print("1) Tallennetaan uusi salasana (rekisteröinti)")
        print("2) Kirjaudutaan (verifiointi)")
        print("0) Lopeta")
        choice = input("Valinta: ").strip()

        if choice == "0":
            print("Lopetetaan.")
            return

        elif choice == "1":
            username = input("\nKäyttäjätunnus: ").strip()

            print("\n1) Salasana syötetään NÄKYVÄSTI (DEMO).")
            password = input("   Salasana (MASKATTAVA / EI SAA NÄYTTÄÄ): ")

            print("\n2) Luodaan SALT (DEMO näyttää tämän).")
            salt = secrets.token_bytes(16)
            show("salt luotu (hex)", salt.hex(), "tallennetaan")
            show("salt luotu (base64)", b64(salt), "tallennetaan")

            print("\n3) Hashataan (näytetään KAIKKI välivaiheet).")
            hashed = pbkdf2_hash_show_all_steps(password, salt, PEPPER)

            print("\n4) Tallennetaan 'tietokantaan' (muistiin) salt + hash.")
            db[username] = (salt, hashed)

            print("\nTallennus: OK")
            print("Tallennetaan: SALT + HASH")
            print("EI tallenneta: PEPPER")
            print("EI SAA NÄYTTÄÄ/lokittaa: SALASANA, PEPPER, DATA (pwd+pepper)")

        elif choice == "2":
            username = input("\nKäyttäjätunnus: ").strip()
            if username not in db:
                print("Tuntematon käyttäjä → väärin, mene pois")
                continue

            stored_salt, stored_hash = db[username]

            print("\n1) Haetaan SALT ja HASH 'tietokannasta' (DEMO näyttää).")
            show("haettu salt (hex)", stored_salt.hex(), "tallennettu")
            show("haettu hash (hex)", stored_hash.hex(), "tallennettu")

            print("\n2) Syötä salasana NÄKYVÄSTI (DEMO).")
            password = input("   Salasana (MASKATTAVA / EI SAA NÄYTTÄÄ): ")

            print("\n3) Lasketaan hash samalla SALTilla ja PEPPERillä (näytetään välivaiheet).")
            computed_hash = pbkdf2_hash_show_all_steps(password, stored_salt, PEPPER)

            print("\n4) Verrataan hasheja (DEMO näyttää arvot).")
            show("stored_hash (hex)", stored_hash.hex(), "tallennettu")
            show("computed_hash (hex)", computed_hash.hex(), "laskettu")

            ok = hmac.compare_digest(stored_hash, computed_hash)
            show("compare_digest tulos", ok, "tuotannossa pelkkä lopputulos riittää")

            if ok:
                print("\n=> oikein, tervetuloa")
            else:
                print("\n=> väärin, mene pois")

        else:
            print("Virheellinen valinta.")

if __name__ == "__main__":
    main()