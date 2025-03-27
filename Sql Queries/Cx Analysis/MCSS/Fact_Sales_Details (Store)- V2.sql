SELECT distinct
   -- a.InvoiceNumber,
	a.Customer_ID
	,cast (concat('S_',a.Customer_ID) as varchar(50)) as [Customer_ID_All]
	,Prod.Product_Type
	,CASE WHEN c.MarketingCommunicationPref ='True'  THEN 1 ELSE 0 END AS MarketingCommunicationPref
	,cc.Customer_Job_Role
	,c.jobRole
	,c.FirstName
	,c.LastName
	,cc.Customer_Company_Name
	,c.Email as [Org Email]
	,cc.Customer_industry_sector
	,cc.Customer_Company_Size
	,a.Set_Id
	
	,a.Order_Product_Total_Cost
	,CAST(CAST( a.Order_Complete_Date AS CHAR(8)) AS DATE) as Order_Complete_Date 
	,pub.Publication_Designation
	,CASE WHEN a.Set_Id IS NOT NULL THEN sc.Set_Title 
     ELSE pub.Publication_Designation END AS [Standard]
	--,CASE when sp.Set_Id is null then 'SS' ELSE 'SBS' end as [Sales_Type]
	, Prod.product_sale_category AS Purchase_Type
	,Subscription_Status 
	,'Store' AS [Type]

     
 FROM [PRES_FACT].[Fact_Order_Product_Current]  a 	  --828
  left  join  PRES_DIM.Dim_SetPublication_Current sp
  on a.Publication_Id = sp.Publication_Id
  left join PRES_DIM.Dim_Customer_Current cc 
  on cc.Customer_ID  = a.Customer_ID
  left join LND_SHOP.[User] c
  on cc.Customer_ID = c.Id
  left join PRES_DIM.Dim_Publication_Current pub
  on a.Publication_Id = pub.Publication_Id
  LEFT JOIN [PRES_DIM].dim_product_current Prod
  ON Prod.product_key = a.product_key
  Left join PRES_DIM.Dim_Set_Current sc 
     on sc.Set_Id = a.Set_Id

  where  a.Order_Status = 'Complete' and a.Customer_ID is not NULL --and a.Set_Id is not NULL  --559174
   and  Customer_Company_Name NOT IN ('NULL','','Standards Australia', 'Test Company','Test company','Terem','SA') 
		and Email NOT LIKE '%testmail%' AND Email NOT LIKE '%terem%' AND Email NOT LIKE '%standards.org.au%'AND Email NOT LIKE '%autotest%'  AND Email NOT LIKE '%sensedata%'
		and pub.Publication_Designation in ('SA TS 5396:2024','SA TS 5397:2024')
		--and a.Set_Id is not null 
		--and a.Customer_ID in(2760)
		--and a.Publication_Id in ('117361','61283','60605','59194','47132','65535','105083')
	order by a.Customer_ID