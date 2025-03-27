--Inputs

DECLARE @SelectedPublicationDesignations TABLE (Publication_Designation NVARCHAR(255));

INSERT INTO @SelectedPublicationDesignations (Publication_Designation)
VALUES 
('AS 5370:2024');
--('iso 22262-1:2012'),
--('iso 22262-3:2016');
--('AS/NZS 1716:2012'),
--('AS/NZS 1269.1:2005'),
--('AS 2832.1:2015'),
--('AS/NZS 2299.1:2015'),
--('AS/NZS ISO 45003:2021'),
--('AS/NZS 3012:2019'),
--('AS 2593:2021'),
--('AS 2397:2015'),
--('AS 4343:2014');



--DECLARE @CustomerID INT; 
--SET @CustomerID = 200; 



--Generate Original Publications Purchased with Customer ID

WITH OriginalPublications AS (
    SELECT distinct
        S.Publication_Id AS OriginalPublicationId,
        P.Publication_URI,
        P.Publication_Designation AS OriginalPublication
       , S.Customer_ID
		--,CASE 
  --          WHEN S.Customer_ID IS NOT NULL THEN 'Purchased'
  --          ELSE 'Not Purchased'
  --      END AS Original_Purchase_Status
 FROM 
        [PRES_FACT].[Fact_Order_Product_Current] S
   JOIN 
        PRES_DIM.Dim_Publication_Current P
        ON S.Publication_Id = P.Publication_Id
  --  WHERE 
        --P.Publication_Designation IN (SELECT Publication_Designation FROM @SelectedPublicationDesignations) -- Filter by the selected designation
		--AND S.Customer_ID = @CustomerID
		--and S.Customer_ID = 35374--35374--59933
		 --AND 
		 --S.Customer_ID = 38421--26964
),
--SELECT * 
--FROM OriginalPublications where Customer_ID is not null;

----Generate the List of Related Publications Based on the Selected Publication Designation
--with OriginalPublications AS (
--    SELECT 
--        P.Publication_Id AS OriginalPublicationId,
--        P.Publication_URI,
--        P.Publication_Designation AS OriginalPublication
		
--    FROM 
--        PRES_DIM.Dim_Publication_Current P
--    WHERE 
--        P.Publication_Designation IN (SELECT Publication_Designation FROM @SelectedPublicationDesignations) -- Filter by the selected designation
--),
RelatedPublications AS (
    SELECT 
        OP.OriginalPublicationId,
		OP.OriginalPublication,
		Op.Customer_ID,
		--OP.Original_Purchase_Status,
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
--FROM RelatedPublications where [Total Score] > 0.3 and Customer_ID is not null

--Generate Related Publications Purchased with Customer ID
SELECT distinct
    RP.*, COALESCE(S.Customer_ID, NULL) AS Customer_ID,
    CASE 
        WHEN S.Customer_ID IS NOT NULL THEN 'Purchased'
        ELSE 'Not Purchased'
    END AS Related_Purchase_Status
FROM 
    RelatedPublications RP
LEFT JOIN 
   [PRES_FACT].[Fact_Order_Product_Current] S
    ON RP.RelatedPublicationId = S.Publication_Id 
	--AND S.Customer_ID = 38421--26964 --35374--59933--626

order by [Total Score] desc

