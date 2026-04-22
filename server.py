import socket

HOST        = '127.0.0.1'
PORT        = 9999
BUFFER_SIZE = 1024

clienti_conectati = {}
mesaje_publicate = {}
urmatorul_id = 1

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print("=" * 50)
print(f"  SERVER UDP pornit pe {HOST}:{PORT}")
print("  Asteptam mesaje de la clienti...")
print("=" * 50)

while True:
    try:
        date_brute, adresa_client = server_socket.recvfrom(BUFFER_SIZE)
        mesaj_primit = date_brute.decode('utf-8').strip()

        parti = mesaj_primit.split(' ', 1)
        comanda = parti[0].upper()
        argumente = parti[1] if len(parti) > 1 else ''

        print(f"\n[PRIMIT] De la {adresa_client}: '{mesaj_primit}'")

        if comanda == 'CONNECT':
            if adresa_client in clienti_conectati:
                raspuns = "EROARE: Esti deja conectat la server."
            else:
                clienti_conectati[adresa_client] = True
                nr_clienti = len(clienti_conectati)
                raspuns = f"OK: Conectat cu succes. Clienti activi: {nr_clienti}"
                print(f"[SERVER] Client nou conectat: {adresa_client}")

        elif comanda == 'DISCONNECT':
            if adresa_client in clienti_conectati:
                del clienti_conectati[adresa_client]
                raspuns = "OK: Deconectat cu succes. La revedere!"
                print(f"[SERVER] Client deconectat: {adresa_client}")
            else:
                raspuns = "EROARE: Nu esti conectat la server."

        elif comanda == 'PUBLISH':
            if adresa_client not in clienti_conectati:
                raspuns = "EROARE: Nu esti conectat la server."
            elif not argumente.strip():
                raspuns = "EROARE: Mesajul pentru PUBLISH nu poate fi gol."
            else:
                id_mesaj = urmatorul_id
                mesaje_publicate[id_mesaj] = {
                    'autor': adresa_client,
                    'text': argumente.strip()
                }
                urmatorul_id += 1
                raspuns = f"OK: Mesaj publicat cu ID={id_mesaj}"

        elif comanda == 'DELETE':
            if adresa_client not in clienti_conectati:
                raspuns = "EROARE: Nu esti conectat la server."
            elif not argumente.strip():
                raspuns = "EROARE: Trebuie sa furnizezi ID-ul mesajului pentru DELETE."
            else:
                try:
                    id_mesaj = int(argumente.strip())

                    if id_mesaj not in mesaje_publicate:
                        raspuns = f"EROARE: Nu exista niciun mesaj cu ID={id_mesaj}."
                    elif mesaje_publicate[id_mesaj]['autor'] != adresa_client:
                        raspuns = "EROARE: Nu poti sterge acest mesaj deoarece nu esti autorul."
                    else:
                        del mesaje_publicate[id_mesaj]
                        raspuns = f"OK: Mesajul cu ID={id_mesaj} a fost sters."
                except ValueError:
                    raspuns = "EROARE: ID-ul pentru DELETE trebuie sa fie un numar intreg valid."

        elif comanda == 'LIST':
            if adresa_client not in clienti_conectati:
                raspuns = "EROARE: Nu esti conectat la server."
            elif not mesaje_publicate:
                raspuns = "OK: Nu exista mesaje publicate."
            else:
                lista_mesaje = []
                for id_mesaj, detalii in mesaje_publicate.items():
                    lista_mesaje.append(f"ID={id_mesaj}: {detalii['text']}")
                raspuns = "\n".join(lista_mesaje)

        else:
            raspuns = f"EROARE: Comanda '{comanda}' este necunoscuta. Comenzi valide: CONNECT, DISCONNECT, PUBLISH, DELETE, LIST"

        server_socket.sendto(raspuns.encode('utf-8'), adresa_client)
        print(f"[TRIMIS]  Catre {adresa_client}: '{raspuns}'")

    except KeyboardInterrupt:
        print("\n[SERVER] Oprire server...")
        break
    except Exception as e:
        print(f"[EROARE] {e}")

server_socket.close()
print("[SERVER] Socket inchis.")