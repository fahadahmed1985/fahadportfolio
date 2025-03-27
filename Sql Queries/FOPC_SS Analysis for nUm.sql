SELECT FOP.InvoiceNumber AS [Order ID]
, c.Customer_ID AS [Customer]
--test
,p.Product_Code
,FOP.Order_Product_Quantity AS Quantity
,FOP.Order_Product_Unit_Cost
,FOP.Order_Product_Total_Unit_Cost*1.1 AS [Extended Price+gst]
,FOP.Order_Product_Total_Unit_Cost-FOP.Order_Product_Unit_Cost as diff
,pub.Publication_Designation AS Designation
,p.Product_Type AS [Product Type]
,FOP.InvoiceNumber AS [Transaction Number]
,P.Product_Licence_Count
,P.Product_Key
,CONVERT(date, CONVERT(varchar(10)
,FOP.Complete_Date_Key, 101)) AS [Transaction Date]
,CONCAT(c.Customer_First_Name, ' ', c.Customer_Last_Name)  AS Name
,c.Customer_Company_Name AS Organisation
,c.Billing_Address_Suburb AS City
,c.Billing_Address_State AS State
,c.Billing_Address_Postcode AS Postcode
,c.Billing_Address_Country AS Country
,c.Customer_Email AS Email
FROM   PRES_FACT.Fact_Order_Product_Current AS FOP LEFT OUTER JOIN
             PRES_DIM.Dim_Publication AS pub ON pub.Publication_Key = FOP.Publication_Key AND pub.ETL_ROW_DELETED_FLAG = 0 AND pub.ETL_ROW_CURRENT_FLAG = 1 LEFT OUTER JOIN
             PRES_DIM.Dim_Product AS p ON p.Product_Key = FOP.Product_Key AND p.COMBINED_ROW_CURRENT_FLAG = 1 LEFT OUTER JOIN
             PRES_DIM.Dim_Customer AS c ON c.Customer_ID = FOP.Customer_ID AND c.COMBINED_ROW_CURRENT_FLAG = 1

WHERE (FOP.Publication_Key IS NOT NULL) AND (FOP.Order_Status = 'Complete')
and Set_Id is null and FOP.Payment_Type = 'Invoice'
and c.Customer_Email not like '%standards.org.au%'
and c.Customer_Email not like '%terem%'
and c.Customer_Company_Name not like 'Standards Australia%'
and c.Customer_Company_Name not like 'SA%'
and Order_Product_Unit_Cost > 0
and c.Customer_ID = 18055
--and c.Customer_Email ='martin.jensen@australisscientific.com'
---and ( FOP.Order_Product_Total_Unit_Cost-FOP.Order_Product_Unit_Cost )>0
order by CONVERT(date, CONVERT(varchar(10), FOP.Complete_Date_Key, 101))

---a.Set_Key IS NOT NULL
--- organise by org and purchase in the last year 

--pricing model of num
--- minimum requirre 5 singles and 2 users NUM < ss purchases 
--  the quantity column > 1 is generally hard copy. 
-- 



----- sumerise version of this :

SELECT 
    c.Customer_ID AS [Customer],
	MAX(P.Product_Licence_Count) AS Total_Licences
    ,SUM(FOP.Order_Product_Total_Unit_Cost) AS Total_Extended_Price,
    Count(pub.Publication_Designation) AS Product_Designation_Count
    ,Count(fop.InvoiceNumber) AS Product_Designation_Count
    --,p.Product_Type as [Product Type]
	--,CONCAT(c.Customer_First_Name, ' ', c.Customer_Last_Name)  AS Name,
 --   c.Customer_Company_Name AS Organisation,
 --   c.Billing_Address_Suburb AS City,
 --   c.Billing_Address_State AS State,
 --   c.Billing_Address_Postcode AS Postcode,
 --   c.Billing_Address_Country AS Country
FROM 
    PRES_FACT.Fact_Order_Product_Current AS FOP 
    LEFT OUTER JOIN PRES_DIM.Dim_Publication AS pub 
        ON pub.Publication_Key = FOP.Publication_Key 
        AND pub.ETL_ROW_DELETED_FLAG = 0 
        AND pub.ETL_ROW_CURRENT_FLAG = 1 
    LEFT OUTER JOIN PRES_DIM.Dim_Product AS p 
        ON p.Product_Key = FOP.Product_Key 
        AND p.COMBINED_ROW_CURRENT_FLAG = 1 
    LEFT OUTER JOIN PRES_DIM.Dim_Customer AS c 
        ON c.Customer_ID = FOP.Customer_ID 
        AND c.COMBINED_ROW_CURRENT_FLAG = 1
WHERE 
    FOP.Publication_Key IS NOT NULL 
    AND Order_Status = 'Complete'
    AND Set_Id IS NULL 
    AND Payment_Type = 'Invoice'
	and Order_Product_Unit_Cost > 0  -- excluding publications with 0 value 
	and p.Product_Licence_Count >1
	--and c.Customer_Email = 'admin@smithtonmetalworx.com.au'
and c.Customer_Email not like '%standards.org.au%'
and c.Customer_Email not like '%terem%'
and c.Customer_Company_Name not like 'Standards Australia%'
and c.Customer_Company_Name not like 'SA%'
and c.Customer_ID = '18055'
GROUP BY 
    c.Customer_ID
	,FOP.Complete_Date_Key
	--,P.Product_Licence_Count
   -- ,p.Product_Type
    --,CONCAT(c.Customer_First_Name, ' ', c.Customer_Last_Name),
    --c.Customer_Company_Name,
    --c.Billing_Address_Suburb,
    --c.Billing_Address_State,
    --c.Billing_Address_Postcode,
    --c.Billing_Address_Country
having SUM(FOP.Order_Product_Total_Unit_Cost) >0 --and COUNT(pub.Publication_Designation) >1
--and CONVERT(date, CONVERT(varchar(10),FOP.Complete_Date_Key, 101)) between '2023-07-01'and '2024-08-01'
order by SUM(FOP.Order_Product_Total_Unit_Cost),COUNT(pub.Publication_Designation)

