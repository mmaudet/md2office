# md2office - Guide d'Utilisation

**Version 0.1.0**

md2office est un outil open source permettant de convertir des fichiers Markdown en documents Word (DOCX) professionnels avec support de templates corporate et mapping de styles.

*[English version available](README.md)*

## Table des matières

1. [Installation](#installation)
2. [Utilisation Rapide](#utilisation-rapide)
3. [Balises Markdown Supportées](#balises-markdown-supportées)
4. [Templates Disponibles](#templates-disponibles)
5. [Mapping des Styles](#mapping-des-styles)
6. [Compatibilité Multi-Templates](#compatibilité-multi-templates)
7. [Variables de Template](#variables-de-template)
8. [API REST](#api-rest)
9. [Configuration Avancée](#configuration-avancée)
10. [Dépannage](#dépannage)
11. [Support](#support)

## Installation

### Avec uv (recommandé)

```bash
# Cloner le dépôt
git clone https://github.com/mmaudet/md2office.git
cd md2office

# Installer les dépendances
uv sync

# Vérifier l'installation
uv run md2office --help
```

### Avec pip

```bash
pip install md2office
```

## Utilisation Rapide

### Ligne de commande

```bash
# Conversion simple
md2office convert document.md

# Avec template spécifique
md2office convert document.md -t professional -o output.docx

# Avec template LINAGORA et variables
md2office convert proposal.md -t linagora -o proposal.docx \
  -v title="Proposition Technique" \
  -v author="Jean Dupont" \
  -v date="2026-01-18"
```

### API Python

```python
from md2office import convert

# Conversion simple
convert("input.md", "output.docx")

# Avec options
convert(
    "proposal.md",
    "proposal.docx",
    template="linagora",
    variables={
        "title": "Proposition Technique",
        "author": "Jean Dupont",
        "date": "2026-01-18"
    }
)
```

## Balises Markdown Supportées

md2office supporte une large gamme de syntaxe Markdown, permettant de créer des documents riches et professionnels.

### Titres (Headings)

Les titres de niveau 1 à 6 sont supportés et correspondent aux styles Word `Heading 1` à `Heading 6`.

```markdown
# Titre niveau 1
## Titre niveau 2
### Titre niveau 3
#### Titre niveau 4
##### Titre niveau 5
###### Titre niveau 6
```

### Formatage de texte

| Markdown | Résultat | Description |
|----------|----------|-------------|
| `**texte**` | **gras** | Mise en gras |
| `*texte*` | *italique* | Mise en italique |
| `***texte***` | ***gras italique*** | Gras et italique |
| `` `code` `` | `code inline` | Police monospace (Liberation Mono) |
| `~~texte~~` | ~~barré~~ | Texte barré |
| `[lien](url)` | [lien cliquable](https://example.com) | Hyperlien cliquable |

### Listes

#### Liste à puces

```markdown
- Premier élément
- Deuxième élément
  - Sous-élément
  - Autre sous-élément
- Troisième élément
```

Résultat :
- Premier élément
- Deuxième élément
  - Sous-élément
  - Autre sous-élément
- Troisième élément

#### Liste numérotée

```markdown
1. Première étape
2. Deuxième étape
   1. Sous-étape A
   2. Sous-étape B
3. Troisième étape
```

Résultat :
1. Première étape
2. Deuxième étape
   1. Sous-étape A
   2. Sous-étape B
3. Troisième étape

### Blocs de code

Les blocs de code sont rendus avec :
- Police monospace (Liberation Mono, 9pt)
- Alignement à gauche forcé
- Chaque ligne dans un paragraphe séparé pour un rendu optimal

```python
def hello_world():
    """Fonction de démonstration."""
    print("Hello, World!")
    return True
```

Le langage spécifié après les trois backticks est conservé pour référence mais n'active pas de coloration syntaxique dans le DOCX.

### Tableaux

Les tableaux Markdown sont convertis en tableaux Word avec :
- En-têtes colorés (configurable)
- Lignes alternées (optionnel)
- Centrage vertical du contenu
- Support des hyperliens cliquables

```markdown
| Colonne A | Colonne B | Colonne C |
|-----------|-----------|-----------|
| Valeur 1  | Valeur 2  | Valeur 3  |
| Valeur 4  | Valeur 5  | Valeur 6  |
```

| Colonne A | Colonne B | Colonne C |
|-----------|-----------|-----------|
| Valeur 1  | Valeur 2  | Valeur 3  |
| Valeur 4  | Valeur 5  | Valeur 6  |

#### Cellules fusionnées

md2office supporte la fusion de cellules avec une syntaxe étendue :

- **Fusion verticale (rowspan)** : Utilisez `^^` pour fusionner une cellule avec celle du dessus
- **Fusion horizontale (colspan)** : Utilisez `>>` pour fusionner une cellule avec celle de gauche

**Exemple de fusion verticale :**

```markdown
| Catégorie | Produit   | Prix  |
|-----------|-----------|-------|
| Fruits    | Pomme     | 1.50€ |
| ^^        | Orange    | 2.00€ |
| ^^        | Banane    | 1.20€ |
| Légumes   | Carotte   | 0.80€ |
| ^^        | Tomate    | 1.50€ |
```

| Catégorie | Produit   | Prix  |
|-----------|-----------|-------|
| Fruits    | Pomme     | 1.50€ |
| ^^        | Orange    | 2.00€ |
| ^^        | Banane    | 1.20€ |
| Légumes   | Carotte   | 0.80€ |
| ^^        | Tomate    | 1.50€ |

**Exemple de fusion horizontale :**

```markdown
| Nom       | Contact   | >>        |
|-----------|-----------|-----------|
| Dupont    | Email     | Téléphone |
| Martin    | email@ex  | 01234567  |
```

| Nom       | Contact   | >>        |
|-----------|-----------|-----------|
| Dupont    | Email     | Téléphone |
| Martin    | email@ex  | 01234567  |

### Citations (Blockquotes)

Les citations utilisent le style `Quote` avec une bordure gauche et une mise en forme italique.

> Ceci est une citation. Elle peut contenir **du formatage** et s'étendre sur plusieurs lignes pour des passages plus longs.

```markdown
> Ceci est une citation. Elle peut contenir **du formatage**
> et s'étendre sur plusieurs lignes.
```

### Admonitions (GitHub-style)

md2office supporte les admonitions au format GitHub, rendues sous forme de tableaux colorés avec icônes et centrage vertical.

> [!NOTE]
> **Tag :** `> [!NOTE]` - Utilisez les notes pour des informations complémentaires utiles au lecteur.

> [!TIP]
> **Tag :** `> [!TIP]` - Les conseils aident les utilisateurs à améliorer leur productivité ou à découvrir des fonctionnalités.

> [!IMPORTANT]
> **Tag :** `> [!IMPORTANT]` - Mettez en avant les informations cruciales que le lecteur ne doit pas manquer.

> [!WARNING]
> **Tag :** `> [!WARNING]` - Avertissez des risques potentiels ou des actions irréversibles.

> [!CAUTION]
> **Tag :** `> [!CAUTION]` - Signalez les dangers ou les actions qui pourraient causer des problèmes.

**Syntaxe Markdown :**

```markdown
> [!NOTE]
> Contenu de la note avec **formatage** possible.

> [!WARNING]
> Contenu de l'avertissement.
```

**Types supportés :** `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`

### Règles horizontales

Les séparateurs horizontaux (`---`, `***`, ou `___`) créent une ligne de démarcation :

---

### Liens

Les liens sont rendus comme de vrais hyperliens cliquables dans le document Word, avec le style standard (bleu souligné). Ils fonctionnent dans les paragraphes ET dans les tableaux.

Visitez le [dépôt GitHub](https://github.com/mmaudet/md2office) pour plus d'informations.

## Templates Disponibles

md2office inclut deux templates prêts à l'emploi :

| Template | Description | Styles principaux |
|----------|-------------|-------------------|
| `professional` | Template business épuré avec accents bleus | Code Block, Body Text |
| `linagora` | Template corporate LINAGORA avec branding rouge | Code, Text body |

### Utilisation des templates

```bash
# Lister les templates disponibles
md2office templates

# Utiliser un template spécifique
md2office convert document.md -t professional
md2office convert document.md -t linagora

# Ajouter un template personnalisé
md2office template-add mon-template.docx --name corporate

# Supprimer un template
md2office template-remove corporate
```

## Mapping des Styles

md2office utilise un système de mapping entre les éléments Markdown et les styles Word. Comprendre ce mapping est essentiel pour créer des templates personnalisés.

### Tableau de correspondance par défaut

| Élément Markdown | Style configuré | Fallback |
|------------------|-----------------|----------|
| `# Titre` | Heading 1 | - |
| `## Titre` | Heading 2 | - |
| `### Titre` | Heading 3 | - |
| `#### Titre` | Heading 4 | - |
| `##### Titre` | Heading 5 | - |
| `###### Titre` | Heading 6 | - |
| Paragraphe | Text body | Body Text, Normal |
| `` `code` `` | Code in line | Code Char |
| Code block | Code | Code Block |
| `- item` | List 1 | List Bullet |
| `1. item` | Numbering 1 | List Number |
| `> citation` | Quote | - |

### Formatage inline

Le formatage inline (gras, italique, etc.) est appliqué directement aux caractères via les propriétés de police Word, indépendamment du style de paragraphe.

## Compatibilité Multi-Templates

md2office gère automatiquement les différences de nommage de styles entre templates grâce à un système de fallback intelligent.

### Comment ça fonctionne

Quand un style configuré n'existe pas dans le template, md2office essaie automatiquement des alternatives :

| Style configuré | Alternatives essayées |
|-----------------|----------------------|
| `Code` | Code → Code Block |
| `Code Block` | Code Block → Code |
| `Text body` | Text body → Body Text → Normal |
| `Body Text` | Body Text → Text body → Normal |
| `List 1` | List 1 → List Bullet → List Paragraph |
| `Numbering 1` | Numbering 1 → List Number → List Paragraph |

### Exemple pratique

Avec la configuration `code.block: "Code"` :
- **Template LINAGORA** : Utilise le style "Code" (existe)
- **Template Professional** : Fallback vers "Code Block" (existe)

Cette compatibilité permet d'utiliser un seul fichier de configuration pour plusieurs templates.

## Création d'un Template Personnalisé

Pour obtenir les meilleurs résultats, votre template DOCX doit définir les styles appropriés.

### Styles requis

Votre template doit inclure au minimum ces styles :

1. **Heading 1 à Heading 6** - Pour les titres
2. **Normal** ou **Text body** - Pour les paragraphes
3. **Code** ou **Code Block** - Pour les blocs de code
4. **List Bullet** ou **List 1** - Pour les listes à puces
5. **List Number** ou **Numbering 1** - Pour les listes numérotées
6. **Quote** - Pour les citations

### Création pas à pas

1. **Ouvrez Word/LibreOffice** et créez un nouveau document
2. **Définissez les styles** via le panneau Styles :
   - Clic droit sur un style → Modifier
   - Configurez la police, taille, couleur, espacement
3. **Ajoutez des en-têtes/pieds de page** avec variables `{{title}}`, `{{date}}`
4. **Testez votre template** avec un document Markdown simple
5. **Sauvegardez** au format `.docx`
6. **Ajoutez à md2office** :
   ```bash
   md2office template-add mon-template.docx --name custom
   ```

### Configuration recommandée des styles

#### Heading 1
- Police : Liberation Sans, 16pt
- Couleur : Rouge (#c00000) ou Bleu (#1B4F72)
- Espacement avant : 12pt, après : 6pt

#### Heading 2
- Police : Liberation Sans, 15pt
- Couleur : Rouge foncé (#8f0a22) ou Bleu (#1F618D)
- Espacement avant : 10pt, après : 5pt

#### Text body / Normal
- Police : Liberation Sans, 12pt
- Couleur : Noir (#000000)
- Interligne : 1.15
- Espacement après : 6pt

#### Code / Code Block
- Police : Liberation Mono, 9pt
- Alignement : **Gauche** (important!)
- Fond : Gris clair (#F5F5F5)

#### Quote
- Police : Liberation Sans, 11pt, italique
- Couleur : Gris (#555555)
- Bordure gauche
- Retrait : 0.5"

## Variables de Template

md2office supporte l'injection de variables dans les templates via la syntaxe Jinja2.

### Variables disponibles

Les variables peuvent être placées dans :
- Corps du document Markdown
- En-têtes et pieds de page du template
- Propriétés du document

### Syntaxe

```
{{variable_name}}
```

### Exemple d'utilisation

**Dans le Markdown :**
```markdown
# Rapport pour {{customer}}

Document préparé par {{author}} le {{date}}.
```

**Commande :**
```bash
md2office convert doc.md \
  -v customer="Entreprise ABC" \
  -v author="Jean Dupont" \
  -v date="18 janvier 2026"
```

### Variables du template LINAGORA

| Variable | Emplacement | Description |
|----------|-------------|-------------|
| `{{title}}` | En-tête | Titre du document |
| `{{subtitle}}` | En-tête | Sous-titre |
| `{{date}}` | En-tête/Pied de page | Date du document |
| `{{author}}` | Pied de page | Auteur |
| `{{customer}}` | Corps | Nom du client |
| `{{project}}` | Corps | Nom du projet |
| `{{version}}` | Pied de page | Version du document |
| `{{classification}}` | Pied de page | Classification (Confidentiel, Public, etc.) |

## API REST

md2office expose une API REST pour l'intégration dans des workflows automatisés.

### Démarrage du serveur

```bash
# Démarrage simple
md2office serve --port 8080

# Avec rechargement automatique (développement)
md2office serve --port 8080 --reload
```

### Endpoints

#### Conversion de Markdown

**POST /api/v1/convert**

```bash
# Avec fichier
curl -X POST http://localhost:8080/api/v1/convert \
  -F "file=@document.md" \
  -F "template=professional" \
  -o output.docx

# Avec JSON
curl -X POST http://localhost:8080/api/v1/convert \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# Hello\n\nWorld",
    "template": "professional",
    "variables": {"author": "John"}
  }' \
  --output output.docx
```

#### Gestion des templates

```bash
# Liste des templates
curl http://localhost:8080/api/v1/templates

# Upload d'un template
curl -X POST http://localhost:8080/api/v1/templates \
  -F "file=@mon_template.docx" \
  -F "name=corporate"

# Suppression
curl -X DELETE http://localhost:8080/api/v1/templates/corporate
```

#### Santé du service

```bash
curl http://localhost:8080/api/v1/health
```

## Configuration Avancée

### Fichier de configuration principal

**config/styles-mapping.yaml :**

```yaml
# Mapping des titres
headings:
  h1: "Heading 1"
  h2: "Heading 2"
  h3: "Heading 3"
  h4: "Heading 4"
  h5: "Heading 5"
  h6: "Heading 6"

# Mapping des paragraphes
paragraph:
  normal: "Text body"
  quote: "Quote"

# Mapping du code
code:
  inline: "Code in line"
  block: "Code"

# Mapping des listes
list_styles:
  bullet: "List 1"
  number: "Numbering 1"

# Configuration des tableaux
table:
  style: "Table Grid"
  header_bg: "c00d2d"       # Couleur de fond de l'en-tête
  header_text: "FFFFFF"     # Couleur du texte de l'en-tête
  alternating_rows: true    # Lignes alternées
  alt_row_bg: "F9F9F9"      # Couleur des lignes alternées

# Configuration des admonitions
admonitions:
  NOTE:
    icon: "i"
    color: "0969DA"
    bg: "DDF4FF"
  TIP:
    icon: "tip"
    color: "1A7F37"
    bg: "DCFFE4"
  IMPORTANT:
    icon: "!"
    color: "8250DF"
    bg: "FBEFFF"
  WARNING:
    icon: "warn"
    color: "9A6700"
    bg: "FFF8C5"
  CAUTION:
    icon: "x"
    color: "CF222E"
    bg: "FFEBE9"
```

## Dépannage

### Les styles ne s'appliquent pas

**Problème :** Le document utilise "Normal" au lieu des styles attendus.

**Solutions :**
1. Vérifiez que votre template contient les styles requis
2. Les noms de styles sont sensibles à la casse
3. md2office essaie automatiquement des alternatives (voir [Compatibilité Multi-Templates](#compatibilité-multi-templates))

### Le texte du code est justifié

**Problème :** Les blocs de code apparaissent avec un texte justifié au lieu d'être alignés à gauche.

**Solution :** Ce problème a été corrigé dans la version 0.1.0. md2office force maintenant l'alignement à gauche sur tous les blocs de code.

### Les listes n'ont pas de puces

**Problème :** Les listes apparaissent sans puces ni numéros.

**Solution :** md2office utilise un préfixe textuel (`-` ou `1.`) plutôt que les puces Word natives pour un rendu cohérent sur tous les templates.

### Les liens ne sont pas cliquables

**Problème :** Les liens apparaissent en bleu mais ne sont pas cliquables.

**Solution :** Depuis la version 0.1.0, les liens sont convertis en vrais hyperliens Word. Assurez-vous d'utiliser la dernière version.

### Les admonitions ne sont pas centrées verticalement

**Problème :** Le texte dans les admonitions n'est pas centré verticalement dans la cellule.

**Solution :** Ce problème a été corrigé dans la version 0.1.0 en supprimant les marges de cellule et en définissant l'espacement des paragraphes à 0.

## Support

| Ressource | Lien |
|-----------|------|
| GitHub Issues | [github.com/mmaudet/md2office/issues](https://github.com/mmaudet/md2office/issues) |
| Documentation | [github.com/mmaudet/md2office](https://github.com/mmaudet/md2office) |
| Guide de contribution | [CONTRIBUTING.md](../CONTRIBUTING.md) |

## Licence

md2office est distribué sous licence Apache 2.0. Voir le fichier [LICENSE](../LICENSE) pour les détails.
