DECLARE @Designations TABLE (Designation VARCHAR(200));

-- Insert the designations you want as input values
INSERT INTO @Designations (Designation)
VALUES 

('AS/NZS 1891.1:2020'),
('AS/NZS 1716:2012'),
('AS/NZS 1269.1:2005'),
('AS 2832.1:2015'),
('AS/NZS 2299.1:2015'),
('AS/NZS ISO 45003:2021'),
('AS/NZS 3012:2019'),
('AS 2593:2021'),
('AS 2397:2015'),
('AS 4343:2014')

--select * from pres_dim.Dim_Set_Current
--select * from pres_dim.Dim_SetPublication_Current

--Store SBS Purchased
SELECT distinct
    a.Customer_ID, FirstName, LastName, Email,Customer_Company_Name, Customer_Marketing_Communication_Pref
	,spc.Publication_Id
	,pc.Publication_Designation
	,a.Set_Id
     
  FROM [PRES_FACT].[Fact_Order_Product_Current] a
  left join PRES_DIM.Dim_Customer_Current b
  on a.Customer_ID = b.Customer_ID
  left join LND_SHOP.[User] c
  on a.Customer_ID = c.Id
  left join pres_dim.Dim_SetPublication_Current spc
  on spc.Set_Id = a.Set_Id
  left join PRES_DIM.Dim_Publication_Current pc
  on spc.Publication_Id = pc.Publication_Id
  
  where 
  pc.Publication_Designation IN (SELECT Designation FROM @Designations)
  and a.Customer_ID is not null and a.Set_Id is not NULL
  and Customer_Company_Name NOT IN ('NULL','','Standards Australia', 'Test Company','Test company')
  order by a.Customer_id