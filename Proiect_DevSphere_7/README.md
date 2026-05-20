# Colectarea de Informații de Sistem de la Distanță (Client-Server Distribuit)

O aplicație distribuită construită în Python pentru colectarea informațiilor de sistem de la mai mulți clienți la distanță. Proiectul utilizează un server centralizat pentru coordonarea cererilor și agregarea rezultatelor, urmând o arhitectură de tip Command & Control (C2).

## Descriere
Acest proiect implementează un sistem distribuit format din:
- **Server**: Orchestrează comunicarea, menține registrul clienților conectați și agregă rezultatele interogărilor.
- **Client Operator**: Orice client conectat poate acționa ca „operator” pentru a compune interogări și a selecta țintele.
- **Client Țintă**: Clienții care primesc și execută interogări simulate de tip WMI, trimițând datele de sistem înapoi la server.

Serverul distribuie cererea către clienții selectați (notificându-i pe rând) și colectează rezultatele **asincron**, utilizând un mecanism robust de timeout per cerere.

## Arhitectură
Fluxul de comunicare urmează o topologie de tip stea centralizată:
1. **Operatorul** trimite `EXECUTE_QUERY` către **Server**.
2. **Serverul** validează cererea și transmite `RUN_QUERY` către **Țintele** selectate (iterând prin listă).
3. **Țintele** execută interogarea și trimit `QUERY_RESULT` înapoi la **Server**.
4. **Serverul** colectează toate răspunsurile (sau gestionează timeout-urile/deconectările) și trimite un `AGGREGATED_RESULT` final către **Operator**.

## Comenzi Suportate (10 Interogări Simulate)
Aplicația suportă următoarele comenzi:

1.  **GET_OS**: Returnează șirul de caractere al platformei sistemului de operare.
2.  **GET_HOSTNAME**: Returnează numele de rețea al mașinii.
3.  **GET_TIME**: Returnează data și ora locală curentă.
4.  **GET_IP**: Returnează adresa IP locală (detectată automat; fallback pe 127.0.0.1 dacă nu există internet).
5.  **GET_PLATFORM**: Returnează tipul sistemului (ex: 'Windows', 'Linux').
6.  **GET_ARCHITECTURE**: Returnează arhitectura procesorului (ex: 'AMD64').
7.  **GET_PROCESSOR**: Returnează numele/detaliile procesorului.
8.  **GET_PYTHON_VERSION**: Returnează versiunea de Python utilizată de client.
9.  **GET_CLIENT_INFO**: Un raport complet (Hostname, IP, OS, Arhitectură, Python).
10. **NO_RESPONSE**: Comandă specială pentru a simula un client care nu răspunde (pentru testarea timeout-ului).

## Mod de Rulare

### 1. Pornirea Serverului (via Docker)
Asigurați-vă că aveți Docker instalat, apoi rulați:
```bash
docker-compose up --build
```
Serverul va începe să asculte pe `0.0.0.0:65432` în interiorul containerului, mapat pe host.

### 2. Pornirea Clienților (Local)
În terminale separate pe mașina dumneavoastră, rulați:
```bash
python client.py
```
*Notă: Clienții se conectează la `127.0.0.1:65432` pentru a ajunge la portul mapat de Docker.*

### 3. Utilizare
- Folosiți meniul interactiv din consola clientului.
- **Opțiunea 1**: Vizualizarea listei curente de clienți conectați.
- **Opțiunea 2**: Trimiterea unei interogări. Veți fi întrebat de comandă și ID-urile țintă (ex: `all` sau `1,3`).
- **Opțiunea 3**: Deconectare curată de la server.

## Scenarii Demo

### Scenariul 1: Actualizări în Timp Real
Conectați 3 clienți succesiv. Observați cum serverul transmite lista actualizată, iar fiecare consolă de client afișează `[UPDATE] Client list updated`.

### Scenariul 2: Interogare Globală
Ca Operator (Client 1), trimiteți `GET_OS` către `all`.
- **Rezultat Așteptat**: Toți cei 3 clienți execută interogarea, iar Operatorul primește un singur raport agregat cu rezultatele de la ID-urile 1, 2 și 3.

### Scenariul 3: Interogare Selectivă
Ca Operator, trimiteți `GET_TIME` către țintele `1,3`.
- **Rezultat Așteptat**: Doar clienții 1 și 3 sunt notificați. Operatorul primește un raport care conține doar cele două rezultate.

### Scenariul 4: Gestionarea Erorilor
Trimiteți o comandă invalidă (`INVALID_QUERY`) către `all`.
- **Rezultat Așteptat**: Clienții țintă returnează un status de `ERROR`, care este afișat corect în raportul agregat final.

### Scenariul 5: Gestionarea Timeout-ului
Trimiteți `NO_RESPONSE` către `all`.
- **Rezultat Așteptat**: Serverul așteaptă 5 secunde. Deoarece niciun client nu răspunde, acesta generează o eroare de „Timeout” pentru fiecare țintă și trimite raportul agregat către Operator.

### Scenariul 6: Deconectare neașteptată
Închideți un client folosind opțiunea 3 din meniu.
- **Rezultat Așteptat**: Serverul elimină clientul și notifică imediat restul clienților. Dacă acel client era țintă pentru o interogare activă, serverul îl marchează ca „Eroare/Deconectat” în raportul final.

## Detalii Tehnice

### Modelul de Threading
- **Server**: Utilizează un model „thread-per-connection”. Un thread dedicat gestionează I/O pentru fiecare socket de client. Un thread separat monitorizează cererile pendinte pentru timeout-uri.
- **Client**: Utilizează un thread de tip „listener” în fundal pentru a primi mesaje asincron de la server, în timp ce thread-ul principal gestionează meniul interactiv.

### ID-uri de Cerere și Agregare
Fiecare interogare validă primește un UUID unic (`request_id`). Serverul urmărește aceste ID-uri într-o mapă `pending_requests`, permițându-i să asocieze corect rezultatele primite cu cererea originală. Rezultatele sunt acceptate doar de la clienții care au făcut parte din lista inițială de ținte.

### Mecanismul de Timeout
Serverul impune un **timeout de 5 secunde** pentru toate interogările. Acest lucru garantează că operatorul primește întotdeauna un răspuns, chiar dacă unii clienți sunt lenți sau s-au deconectat neașteptat.

### Notă despre Simularea WMI
Interogările WMI reale sunt limitate la Windows. Acest proiect utilizează bibliotecile `platform`, `socket` și `datetime` pentru a **simula** descoperirea sistemului, făcând aplicația portabilă pe Windows, Linux și macOS.
