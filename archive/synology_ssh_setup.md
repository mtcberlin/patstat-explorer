# SSH Key Setup für Synology (ohne Passwort)

## Übersicht
- **Synology IP**: 192.168.102.129
- **Benutzer**: arnekrueger
- **PATSTAT Daten**: /volume1/archive/patstat/

## Einmalige Einrichtung

### 1. Synology: Home-Verzeichnis aktivieren
1. Web-GUI öffnen: http://192.168.102.129:5000
2. **Systemsteuerung** → **Benutzer & Gruppe** → **Erweitert**
3. ✅ **"Benutzer-Home-Dienst aktivieren"** ankreuzen
4. Speichern

### 2. Mac: SSH-Key generieren & installieren

```bash
# SSH-Key generieren (ohne Passphrase)
ssh-keygen -t ed25519 -f ~/.ssh/id_synology -N ""

# Public Key zur Synology kopieren (braucht EINMAL das Passwort)
ssh-copy-id -i ~/.ssh/id_synology arnekrueger@192.168.102.129

# Testen (sollte OHNE Passwort funktionieren)
ssh -i ~/.ssh/id_synology arnekrueger@192.168.102.129 "hostname"
```

### 3. SSH Config für einfacheren Zugriff (optional)

```bash
# ~/.ssh/config bearbeiten
cat >> ~/.ssh/config << 'EOF'

Host synology
    HostName 192.168.102.129
    User arnekrueger
    IdentityFile ~/.ssh/id_synology
    ServerAliveInterval 60
EOF

# Dann einfach:
ssh synology
```

## Verwendung

### Einfacher SSH-Zugriff
```bash
# Mit Key-File
ssh -i ~/.ssh/id_synology arnekrueger@192.168.102.129

# Mit Config (wenn angelegt)
ssh synology
```

### rsync von Synology
```bash
# Mit Key-File
rsync -avh --progress \
  -e "ssh -i ~/.ssh/id_synology" \
  arnekrueger@192.168.102.129:/volume1/archive/patstat/ \
  ~/local_folder/

# Mit Config (wenn angelegt)
rsync -avh --progress \
  synology:/volume1/archive/patstat/ \
  ~/local_folder/
```

### Dateien browsen
```bash
# Verzeichnis auflisten
ssh -i ~/.ssh/id_synology arnekrueger@192.168.102.129 "ls -lh /volume1/archive/patstat"

# Mit Config
ssh synology "ls -lh /volume1/archive/patstat"
```

## Für 1Password speichern

**Titel**: Synology SSH Key (Mac/MacBook)

**Felder**:
- Server: 192.168.102.129
- User: arnekrueger
- Key Location: ~/.ssh/id_synology
- SSH Command: `ssh -i ~/.ssh/id_synology arnekrueger@192.168.102.129`
- PATSTAT Path: /volume1/archive/patstat/

**Anhang**:
- Private Key: ~/.ssh/id_synology (Datei hochladen)
- Public Key: ~/.ssh/id_synology.pub (Datei hochladen)

## MacBook Setup (neues Gerät)

```bash
# 1. Private Key aus 1Password auf neues MacBook kopieren
# Datei speichern als: ~/.ssh/id_synology

# 2. Korrekte Permissions setzen
chmod 600 ~/.ssh/id_synology

# 3. Testen
ssh -i ~/.ssh/id_synology arnekrueger@192.168.102.129 "hostname"

# 4. Optional: SSH Config kopieren (siehe oben)
```

## Troubleshooting

**"Permission denied"**
```bash
# Prüfen ob Key korrekte Permissions hat
ls -l ~/.ssh/id_synology
# Sollte: -rw------- (600)

# Falls nicht:
chmod 600 ~/.ssh/id_synology
```

**"No such file or directory" (Home-Verzeichnis)**
→ Schritt 1 nochmal prüfen (Home-Dienst aktivieren)

**Key funktioniert nicht mehr**
```bash
# Neu installieren
ssh-copy-id -i ~/.ssh/id_synology arnekrueger@192.168.102.129
```
