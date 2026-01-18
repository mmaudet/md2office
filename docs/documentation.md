# md2office - Guide d'Utilisation

**Version 0.1.0**

md2office est un outil open source permettant de convertir des fichiers Markdown en documents Word (DOCX) professionnels avec support de templates corporate et mapping de styles.

## Installation

### Avec uv (recommandé)

```bash
uv add md2office
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

# Avec template et variables
md2office convert document.md -t professional -o output.docx -v title="Mon Rapport" -v author="Jean Dupont"
```

### API Python

```python
from md2office import convert

# Conversion simple
docx_bytes = convert("# Mon Titre\n\nMon contenu")

# Avec options
docx_bytes = convert(
    markdown_text,
    template="professional",
    variables={"title": "Mon Rapport", "date": "2026-01-18"}
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

| Markdown | Résultat | Style Word |
|----------|----------|------------|
| `**texte**` | **gras** | Bold |
| `*texte*` | *italique* | Italic |
| `***texte***` | ***gras italique*** | Bold + Italic |
| `` `code` `` | `code inline` | Consolas font |
| `~~texte~~` | ~~barré~~ | Strikethrough |
| `[lien](url)` | [lien cliquable](https://example.com) | Hyperlink |

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

Les blocs de code sont rendus avec une police monospace (Consolas) et un fond gris clair dans le template professionnel.

```python
def hello_world():
    """Fonction de démonstration."""
    print("Hello, World!")
    return True
```

Le langage spécifié après les trois backticks est conservé pour référence mais n'active pas de coloration syntaxique dans le DOCX.

### Tableaux

Les tableaux Markdown sont convertis en tableaux Word avec en-têtes stylés.

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

**Exemple combiné :**

```markdown
| Trimestre | Q1    | Q2    | Q3    |
|-----------|-------|-------|-------|
| Ventes    | 100   | 150   | 200   |
| Total     | 450   | >>    | >>    |
```

| Trimestre | Q1    | Q2    | Q3    |
|-----------|-------|-------|-------|
| Ventes    | 100   | 150   | 200   |
| Total     | 450   | >>    | >>    |

### Citations (Blockquotes)

Les citations utilisent le style `Quote` avec une bordure gauche et une mise en forme italique.

> Ceci est une citation. Elle peut contenir **du formatage** et s'étendre sur plusieurs lignes pour des passages plus longs.

```markdown
> Ceci est une citation. Elle peut contenir **du formatage**
> et s'étendre sur plusieurs lignes.
```

### Admonitions (GitHub-style)

md2office supporte les admonitions au format GitHub, rendues sous forme de tableaux colorés avec icônes.

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
> Contenu de la note.

> [!WARNING]
> Contenu de l'avertissement.
```

**Types supportés :** `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`

### Règles horizontales

Les séparateurs horizontaux (`---`, `***`, ou `___`) créent une ligne de démarcation.

---

### Liens

Les liens sont rendus comme de vrais hyperliens cliquables dans le document Word, avec le style standard (bleu souligné).

Visitez le [dépôt GitHub](https://github.com/mmaudet/md2office) pour plus d'informations.

## Mapping des Styles

md2office utilise un système de mapping entre les éléments Markdown et les styles Word. Comprendre ce mapping est essentiel pour créer des templates personnalisés.

### Tableau de correspondance

| Élément Markdown | Style Word | Description |
|------------------|------------|-------------|
| `# Titre` | Heading 1 | Titre principal |
| `## Titre` | Heading 2 | Sous-titre |
| `### Titre` | Heading 3 | Section |
| `#### Titre` | Heading 4 | Sous-section |
| `##### Titre` | Heading 5 | Sous-sous-section |
| `###### Titre` | Heading 6 | Paragraphe titré |
| Paragraphe | Normal | Texte standard |
| `` `code` `` | Code Char | Code inline |
| Code block | Code Block | Bloc de code |
| `- item` | List Bullet | Liste à puces |
| `1. item` | List Number | Liste numérotée |
| `> citation` | Quote | Citation |

### Formatage inline

Le formatage inline (gras, italique, etc.) est appliqué directement aux caractères via les propriétés de police Word, indépendamment du style de paragraphe.

## Création d'un Template Personnalisé

Pour obtenir les meilleurs résultats, votre template DOCX doit définir les styles appropriés.

### Styles requis

Votre template doit inclure les styles suivants :

1. **Heading 1 à Heading 6** - Pour les titres
2. **Normal** - Pour les paragraphes
3. **Code Block** - Pour les blocs de code
4. **List Bullet** - Pour les listes à puces
5. **List Number** - Pour les listes numérotées
6. **Quote** - Pour les citations

### Création pas à pas

1. **Ouvrez Word** et créez un nouveau document
2. **Définissez les styles** via le panneau Styles :
   - Clic droit sur un style > Modifier
   - Configurez la police, taille, couleur, espacement
3. **Testez votre template** avec un document Markdown simple
4. **Sauvegardez** au format `.docx`

### Exemple de configuration recommandée

#### Heading 1
- Police : Calibri Light, 28pt
- Couleur : Bleu foncé (#1B4F72)
- Espacement avant : 24pt, après : 12pt
- Bordure inférieure

#### Heading 2
- Police : Calibri Light, 22pt
- Couleur : Bleu (#1F618D)
- Espacement avant : 18pt, après : 10pt

#### Normal
- Police : Calibri, 11pt
- Couleur : Gris foncé (#333333)
- Interligne : 1.15
- Espacement après : 8pt

#### Code Block
- Police : Consolas, 9.5pt
- Fond : Gris clair (#F5F5F5)
- Retrait gauche/droite : 0.25"

#### Quote
- Police : Georgia, 11pt, italique
- Couleur : Gris (#555555)
- Bordure gauche grise
- Retrait : 0.5"

## Variables de Template

md2office supporte l'injection de variables dans les templates via la syntaxe Jinja2.

### Variables disponibles

Les variables peuvent être placées dans :
- En-têtes et pieds de page
- Corps du document
- Propriétés du document

### Syntaxe

```
{{variable_name}}
```

### Exemple d'utilisation

**Template :**
```
En-tête : {{title}}
Pied de page : {{author}} - Page X
```

**Commande :**
```bash
md2office convert doc.md -v title="Rapport Annuel" -v author="Équipe Technique"
```

### Variables du template professionnel

Le template `professional` inclut ces variables :

| Variable | Emplacement | Description |
|----------|-------------|-------------|
| `{{title}}` | En-tête | Titre du document |
| `{{date}}` | En-tête | Date du document |
| `{{author}}` | Pied de page | Auteur ou organisation |

## API REST

md2office expose une API REST pour l'intégration dans des workflows automatisés.

### Démarrage du serveur

```bash
md2office serve --port 8080
```

### Endpoints

#### Conversion de Markdown

```bash
curl -X POST http://localhost:8080/api/v1/convert \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# Hello\n\nWorld", "filename": "output.docx"}' \
  --output output.docx
```

#### Gestion des templates

```bash
# Liste des templates
curl http://localhost:8080/api/v1/templates

# Upload d'un template
curl -X POST http://localhost:8080/api/v1/templates \
  -F "data=@mon_template.docx" \
  -F "name=corporate"

# Suppression
curl -X DELETE http://localhost:8080/api/v1/templates/corporate
```

## Configuration Avancée

### Fichier de configuration

md2office utilise des fichiers YAML pour la configuration des styles et des couleurs d'admonitions.

**config/styles-mapping.yaml :**

```yaml
styles:
  heading:
    h1: "Heading 1"
    h2: "Heading 2"
    h3: "Heading 3"
  paragraph: "Normal"
  code_block: "Code Block"
  list_bullet: "List Bullet"
  list_number: "List Number"
  quote: "Quote"

admonitions:
  NOTE:
    color: "0969DA"
    bg: "DDF4FF"
  WARNING:
    color: "9A6700"
    bg: "FFF8C5"
  CAUTION:
    color: "CF222E"
    bg: "FFEBE9"
```

## Dépannage

### Les styles ne s'appliquent pas

Vérifiez que votre template contient bien les styles requis avec les noms exacts (sensibles à la casse).

### Les listes n'ont pas de puces

Assurez-vous que les styles `List Bullet` et `List Number` sont correctement définis dans votre template.

### Les liens ne sont pas cliquables

Depuis la version 0.1.0, les liens sont convertis en vrais hyperliens Word. Assurez-vous d'utiliser la dernière version.

## Support

| Ressource | Lien |
|-----------|------|
| GitHub Issues | [github.com/mmaudet/md2office/issues](https://github.com/mmaudet/md2office/issues) |
| Documentation | [github.com/mmaudet/md2office](https://github.com/mmaudet/md2office) |

## Licence

md2office est distribué sous licence Apache 2.0.
