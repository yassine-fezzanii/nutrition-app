/* ============================================================
   EXTENSION NUTRITIONNELLE - GClinique_MarocOLIV
   A exécuter sur la base existante (SSMS) - ne touche à aucune
   table existante (Fiche_technique, Detaille_Fiche_Technique,
   Nature_article_Cuisine ne sont pas modifiées).
   ============================================================ */

USE [GClinique_MarocOLIV]
GO

/* ------------------------------------------------------------
   1) Référentiel nutritionnel (type CIQUAL) - valeurs pour 100 g
   ------------------------------------------------------------ */
IF OBJECT_ID('dbo.Table_Composition_Nutritionnelle', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Table_Composition_Nutritionnelle](
        [Code_Nutriment]   [nvarchar](10)  NOT NULL,   -- code interne (ex: N0001)
        [Libelle]          [nvarchar](150) NOT NULL,   -- ex: 'Ail, cru'
        [Calories_100g]    [decimal](10,2) NOT NULL DEFAULT 0,  -- kcal
        [Proteines_100g]   [decimal](10,2) NOT NULL DEFAULT 0,  -- g
        [Lipides_100g]     [decimal](10,2) NOT NULL DEFAULT 0,  -- g
        [Glucides_100g]    [decimal(10,2)] NOT NULL DEFAULT 0,  -- g
        [Fibres_100g]      [decimal](10,2) NOT NULL DEFAULT 0,  -- g
        [Sodium_100g]      [decimal](10,2) NOT NULL DEFAULT 0,  -- mg
        [Source]           [nvarchar](30)  NOT NULL DEFAULT 'CIQUAL',
        CONSTRAINT [PK_Table_Composition_Nutritionnelle] PRIMARY KEY CLUSTERED ([Code_Nutriment] ASC)
    )
END
GO

/* ------------------------------------------------------------
   2) Table de correspondance : article de cuisine -> code nutriment
      (un article Nature_article_Cuisine peut ne pas encore être
      mappé -> jointure LEFT dans la vue de calcul)
   ------------------------------------------------------------ */
IF OBJECT_ID('dbo.Article_Nutrition', 'U') IS NULL
BEGIN
    CREATE TABLE [dbo].[Article_Nutrition](
        [Codart]         [nvarchar](50) NOT NULL,
        [Code_Nutriment] [nvarchar](10) NOT NULL,
        CONSTRAINT [PK_Article_Nutrition] PRIMARY KEY CLUSTERED ([Codart] ASC),
        CONSTRAINT [FK_ArtNut_Article] FOREIGN KEY ([Codart])
            REFERENCES [dbo].[Nature_article_Cuisine]([Code]),
        CONSTRAINT [FK_ArtNut_Nutriment] FOREIGN KEY ([Code_Nutriment])
            REFERENCES [dbo].[Table_Composition_Nutritionnelle]([Code_Nutriment])
    )
END
GO

/* ------------------------------------------------------------
   3) Fonction de conversion d'unité -> grammes / millilitres
      KG, GR, LT, CL, UN (unité -> poids moyen approx. si connu)
   ------------------------------------------------------------ */
IF OBJECT_ID('dbo.fn_Quantite_En_Grammes', 'FN') IS NOT NULL
    DROP FUNCTION dbo.fn_Quantite_En_Grammes
GO
CREATE FUNCTION dbo.fn_Quantite_En_Grammes
(
    @Quantite decimal(18,3),
    @Unite nvarchar(2)
)
RETURNS decimal(18,3)
AS
BEGIN
    DECLARE @Result decimal(18,3)

    SET @Result = CASE UPPER(@Unite)
        WHEN 'KG' THEN @Quantite * 1000.0
        WHEN 'GR' THEN @Quantite
        WHEN 'LT' THEN @Quantite * 1000.0   -- approx. 1L = 1000g (densité eau)
        WHEN 'CL' THEN @Quantite * 10.0
        WHEN 'UN' THEN @Quantite * 100.0    -- poids moyen par défaut d'une unité, à affiner par article
        ELSE @Quantite
    END

    RETURN @Result
END
GO

/* ------------------------------------------------------------
   4) Vue : détail nutritionnel par ligne d'ingrédient de fiche
   ------------------------------------------------------------ */
IF OBJECT_ID('dbo.vw_Nutrition_Ingredient', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Nutrition_Ingredient
GO
CREATE VIEW dbo.vw_Nutrition_Ingredient AS
SELECT
    d.Code_Fiche,
    d.Code_regime,
    d.Codart,
    a.Designation                                              AS Designation_Article,
    d.Unite_Grammage,
    d.Quantite,
    dbo.fn_Quantite_En_Grammes(d.Quantite, d.Unite_Grammage)    AS Quantite_Grammes,
    ISNULL(c.Calories_100g, 0)                                  AS Calories_100g,
    ISNULL(c.Proteines_100g, 0)                                 AS Proteines_100g,
    ISNULL(c.Lipides_100g, 0)                                   AS Lipides_100g,
    ISNULL(c.Glucides_100g, 0)                                  AS Glucides_100g,
    ISNULL(c.Fibres_100g, 0)                                    AS Fibres_100g,
    ISNULL(c.Sodium_100g, 0)                                    AS Sodium_100g,
    (dbo.fn_Quantite_En_Grammes(d.Quantite, d.Unite_Grammage) * ISNULL(c.Calories_100g, 0))  / 100.0 AS Calories,
    (dbo.fn_Quantite_En_Grammes(d.Quantite, d.Unite_Grammage) * ISNULL(c.Proteines_100g, 0)) / 100.0 AS Proteines,
    (dbo.fn_Quantite_En_Grammes(d.Quantite, d.Unite_Grammage) * ISNULL(c.Lipides_100g, 0))   / 100.0 AS Lipides,
    (dbo.fn_Quantite_En_Grammes(d.Quantite, d.Unite_Grammage) * ISNULL(c.Glucides_100g, 0))  / 100.0 AS Glucides,
    (dbo.fn_Quantite_En_Grammes(d.Quantite, d.Unite_Grammage) * ISNULL(c.Fibres_100g, 0))    / 100.0 AS Fibres,
    (dbo.fn_Quantite_En_Grammes(d.Quantite, d.Unite_Grammage) * ISNULL(c.Sodium_100g, 0))    / 100.0 AS Sodium,
    CASE WHEN c.Code_Nutriment IS NULL THEN 0 ELSE 1 END        AS Est_Mappe
FROM dbo.Detaille_Fiche_Technique d
LEFT JOIN dbo.Nature_article_Cuisine a       ON a.Code = d.Codart
LEFT JOIN dbo.Article_Nutrition an           ON an.Codart = d.Codart
LEFT JOIN dbo.Table_Composition_Nutritionnelle c ON c.Code_Nutriment = an.Code_Nutriment
GO

/* ------------------------------------------------------------
   5) Vue : totaux nutritionnels par fiche technique
   ------------------------------------------------------------ */
IF OBJECT_ID('dbo.vw_Nutrition_Fiche', 'V') IS NOT NULL
    DROP VIEW dbo.vw_Nutrition_Fiche
GO
CREATE VIEW dbo.vw_Nutrition_Fiche AS
SELECT
    f.Code                          AS Code_Fiche,
    f.Designation,
    f.Nombre_Personne,
    SUM(v.Calories)                 AS Calories_Total,
    SUM(v.Proteines)                AS Proteines_Total,
    SUM(v.Lipides)                  AS Lipides_Total,
    SUM(v.Glucides)                 AS Glucides_Total,
    SUM(v.Fibres)                   AS Fibres_Total,
    SUM(v.Sodium)                   AS Sodium_Total,
    CASE WHEN f.Nombre_Personne > 0 THEN SUM(v.Calories)  / f.Nombre_Personne ELSE 0 END AS Calories_Personne,
    CASE WHEN f.Nombre_Personne > 0 THEN SUM(v.Proteines) / f.Nombre_Personne ELSE 0 END AS Proteines_Personne,
    CASE WHEN f.Nombre_Personne > 0 THEN SUM(v.Lipides)   / f.Nombre_Personne ELSE 0 END AS Lipides_Personne,
    CASE WHEN f.Nombre_Personne > 0 THEN SUM(v.Glucides)  / f.Nombre_Personne ELSE 0 END AS Glucides_Personne,
    CASE WHEN f.Nombre_Personne > 0 THEN SUM(v.Fibres)    / f.Nombre_Personne ELSE 0 END AS Fibres_Personne,
    CASE WHEN f.Nombre_Personne > 0 THEN SUM(v.Sodium)    / f.Nombre_Personne ELSE 0 END AS Sodium_Personne,
    MIN(v.Est_Mappe)                AS Tous_Ingredients_Mappes  -- 0 si au moins un ingrédient sans donnée nutritionnelle
FROM dbo.Fiche_technique f
JOIN dbo.vw_Nutrition_Ingredient v ON v.Code_Fiche = f.Code
GROUP BY f.Code, f.Designation, f.Nombre_Personne
GO

/* ------------------------------------------------------------
   6) Procédure stockée : nutrition d'une fiche donnée
   ------------------------------------------------------------ */
IF OBJECT_ID('dbo.sp_Get_Nutrition_Fiche', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_Get_Nutrition_Fiche
GO
CREATE PROCEDURE dbo.sp_Get_Nutrition_Fiche
    @Code_Fiche nvarchar(10)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT * FROM dbo.vw_Nutrition_Fiche WHERE Code_Fiche = @Code_Fiche;
    SELECT * FROM dbo.vw_Nutrition_Ingredient WHERE Code_Fiche = @Code_Fiche;
END
GO

/* ------------------------------------------------------------
   7) Exemple de données (à adapter/compléter avec CIQUAL)
   ------------------------------------------------------------ */
IF NOT EXISTS (SELECT 1 FROM dbo.Table_Composition_Nutritionnelle WHERE Code_Nutriment = 'N0001')
BEGIN
    INSERT INTO dbo.Table_Composition_Nutritionnelle
        (Code_Nutriment, Libelle, Calories_100g, Proteines_100g, Lipides_100g, Glucides_100g, Fibres_100g, Sodium_100g)
    VALUES
        ('N0001', 'Ail, cru',                149.0, 6.4,  0.5,  33.0, 4.1,  17.0),
        ('N0002', 'Huile d''olive',           884.0, 0.0,  100.0, 0.0, 0.0,  2.0),
        ('N0003', 'Riz basmati, cuit',        130.0, 2.7,  0.3,  28.0, 0.4,  1.0),
        ('N0004', 'Persil, frais',            36.0,  3.0,  0.8,  6.3,  3.3,  56.0),
        ('N0005', 'Coriandre, fraîche',       23.0,  2.1,  0.5,  3.7,  2.8,  46.0),
        ('N0006', 'Beurre',                   717.0, 0.9,  81.1, 0.7,  0.0,  11.0),
        ('N0007', 'Sel',                      0.0,   0.0,  0.0,  0.0,  0.0,  38758.0),
        ('N0008', 'Poivre noir moulu',        251.0, 10.4, 3.3,  64.0, 25.0, 20.0),
        ('N0009', 'Citron confit',            29.0,  1.1,  0.3,  9.3,  2.8,  2.0),
        ('N0010', 'Thym, sec',                276.0, 9.1,  7.4,  63.9, 37.0, 55.0)
END
GO

-- Mapping de démonstration pour la fiche FT000025 (Calamars farcis au riz basmati)
IF NOT EXISTS (SELECT 1 FROM dbo.Article_Nutrition WHERE Codart = 'HACND0001')
BEGIN
    INSERT INTO dbo.Article_Nutrition (Codart, Code_Nutriment) VALUES
        ('HACND0001', 'N0001'),  -- AIL
        ('HAUIU0002', 'N0002'),  -- HUILE D'OLIVE (adapter au vrai code)
        ('PLRIZ0007', 'N0003'),  -- RIZ BASMATI
        ('PFLEG0018', 'N0004'),  -- PERSIL
        ('PFLEG0019', 'N0005'),  -- CORIANDRE
        ('PFBER0001', 'N0006'),  -- BEURRE EN VRAC
        ('HACND0011', 'N0007'),  -- SEL
        ('HAEPI0024', 'N0008'),  -- POIVRE NOIR MOULU
        ('HACND0012', 'N0009'),  -- CITRON CONFIT
        ('HACND0011', 'N0010')   -- THYM (attention: code démo, à vérifier/dédoublonner)
END
GO
