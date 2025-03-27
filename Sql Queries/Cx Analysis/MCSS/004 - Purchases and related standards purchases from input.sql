--Inputs

DECLARE @SelectedPublicationDesignations TABLE (Publication_Designation NVARCHAR(255));

INSERT INTO @SelectedPublicationDesignations (Publication_Designation)
VALUES 
('AS/NZS 3000:2018'),
('AS 1428.1:2021'),
('AS 1684.2:2021'),
('AS/NZS 5033:2021'),
('AS/NZS 6400:2016'),
('AS 5369:2023'),
('AS ISO 31000:2018'),
('AS 3740:2021'),
('AS 1288:2021'),
('AS/NZS ISO 9001:2016'),
('AS/NZS ISO 45001:2018'),
('AS 4811:2022'),
('AS/NZS 3760:2022'),
('AS 8001:2021'),
('ISO 9001:2015');


DECLARE @CustomerID INT; 
SET @CustomerID = 200; 



--Generate Original Publications Purchased with Customer ID

WITH OriginalPublications AS (
    SELECT 
        S.Publication_Id AS OriginalPublicationId,
        P.Publication_URI,
        P.Publication_Designation AS OriginalPublication,
        S.Customer_ID
 FROM 
        [PRES_FACT].[Fact_Order_Product_Current] S
    JOIN 
        PRES_DIM.Dim_Publication_Current P
        ON S.Publication_Id = P.Publication_Id
    WHERE 
        P.Publication_Designation IN (SELECT Publication_Designation FROM @SelectedPublicationDesignations) -- Filter by the selected designation
		--AND S.Customer_ID = @CustomerID
)
SELECT * 
FROM OriginalPublications where Customer_ID is not null;

--Generate the List of Related Publications Based on the Selected Publication Designation
WITH OriginalPublications AS (
    SELECT 
        P.Publication_Id AS OriginalPublicationId,
        P.Publication_URI,
        P.Publication_Designation AS OriginalPublication
		
    FROM 
        PRES_DIM.Dim_Publication_Current P
    WHERE 
        P.Publication_Designation IN (SELECT Publication_Designation FROM @SelectedPublicationDesignations) -- Filter by the selected designation
),
RelatedPublications AS (
    SELECT 
        OP.OriginalPublicationId,
		OP.OriginalPublication,
        RP.[Related URI],
        P2.Publication_Id AS RelatedPublicationId,
        P2.Publication_Designation AS RelatedPublication,
		Rp.[Total Score]
    FROM 
        OriginalPublications OP
    JOIN 
        [STG_REC].[TEMP_COMB_EXP_HRE_Webview_FB] RP
        ON OP.Publication_URI = RP.URI and RP.[Total Score] <> 0 and Rp.URI<>rp.[Related URI]
    JOIN 
        PRES_DIM.Dim_Publication_Current P2
        ON RP.[Related URI] = P2.Publication_URI
)
--SELECT distinct * 
--FROM RelatedPublications;

--Generate Related Publications Purchased with Customer ID
SELECT 
    RP.*, S.Customer_ID,
    CASE 
        WHEN S.Customer_ID IS NOT NULL THEN 'Purchased'
        ELSE 'Not Purchased'
    END AS PurchaseStatus
FROM 
    RelatedPublications RP
LEFT JOIN 
   [PRES_FACT].[Fact_Order_Product_Current] S
    ON RP.RelatedPublicationId = S.Publication_Id 
	--AND S.Customer_ID = @CustomerID

order by [Total Score] desc

