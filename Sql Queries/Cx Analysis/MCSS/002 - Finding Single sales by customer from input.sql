DECLARE @Designations TABLE (Designation VARCHAR(200));

-- Insert the designations you want as input values
INSERT INTO @Designations (Designation)
VALUES 

('SA TS 5397:2024'),
('SA TS 5397:2024')
--,('AS/NZS 1269.1:2005'),
--('AS 2832.1:2015'),
--('AS/NZS 2299.1:2015'),
--('AS/NZS ISO 45003:2021'),
--('AS/NZS 3012:2019'),
--('AS 2593:2021'),
--('AS 2397:2015'),
--('AS 4343:2014')

--Store SS Purchased
SELECT distinct
    a.Customer_ID, FirstName, LastName, Email,Customer_Company_Name, Customer_Marketing_Communication_Pref,pc.Publication_Designation
	,a.Order_Product_Quantity
     
  FROM [PRES_FACT].[Fact_Order_Product_Current] a
  left join PRES_DIM.Dim_Customer_Current b
  on a.Customer_ID = b.Customer_ID
  left join LND_SHOP.[User] c
  on a.Customer_ID = c.Id
  left join PRES_DIM.Dim_Publication_Current pc
  on a.Publication_Id = pc.Publication_Id
  
  where-- pc.Publication_Designation IN (SELECT Designation FROM @Designations) and
  --and 
  a.Customer_ID is not null and a.Set_Id is null
  and Customer_Company_Name NOT IN ('NULL','','Standards Australia', 'Test Company','Test company')
  order by a.Order_Product_Quantity desc

  ----Another query:

  WITH OriginalPublications AS (
    -- Get all original publications purchased by the specified customer
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
        S.Customer_ID = 200 -- Specify the customer ID here
)

SELECT * 
FROM OriginalPublications;