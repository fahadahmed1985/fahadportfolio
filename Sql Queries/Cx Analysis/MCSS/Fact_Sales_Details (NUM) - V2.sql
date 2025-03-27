WITH FilteredOpportunities AS (
    SELECT distinct
        CAST(O.opportunityclosedate  AS DATE) as Order_Complete_Date,
        O.catlgsalesorderaccountkey,
        O.activesubflag,
        O.accountid,
        O.TotalCustomerPrice,
		O.Primary_Contact_Title,
		O.AccountFullName,
		O.Industry,
        OrgUsers.UserID,
        CASE WHEN OrgUsers.MarketingConsentAcceptedTime IS NOT NULL THEN 1 ELSE 0 END AS MarketingCommunicationPref,
        OrgUsers.organisationid
		,OrgUsers.FirstName
		,OrgUsers.LastName
--		,pu.Email [Email included in Package]
		,OrgUsers.Email as [Org Email]
		, case when pu.Email is null then 'In Active Pkg User' ELSE 'Active Pkg User' END AS [NUM_Active User Status]
		, O.activesubflag as [Subscription_Status]
		, 'NUM' AS Purchase_Type
        , 'Custom Subscription' AS [Type]
		,Convert(varchar(max),A.numberofemployees) AS Customer_Company_Size
    FROM 
       [PRES_FACT].[fact_sf_opportunity] O 
	LEFT JOIN 
	   [PRES_DIM].[dim_sws_organisations] Org 
		ON O.accountid = Org.SalesforceId
    JOIN 
        [PRES_DIM].[dim_sws_orgusers] OrgUsers 
		ON Org.id = OrgUsers.organisationid

	LEFT  JOIN	[PRES_DIM].[DIM_SWS_PackageUsers] PU
		ON	OrgUsers.UserID = PU.UserId
	JOIN [PRES_SF].[account_current] A
       ON A.id = O.accountid
    WHERE 
       -- O.activesubflag = 'True' and 
        
		OrgUsers.userid IS NOT NULL
),
PackageDetails AS (
    SELECT 
        P.packageid,
        P.catlgsalesorderaccountkey,
--		p.OrgName,
--		org.Name,
	--	OrgUsers.Email as [Org Email],
	--	pu.Email as [PU email],
		PP.packageid AS PublicationPackageId,
        PP.uri
		,Publ.Publication_Designation
		,Publ.Publication_Id
		--,sp.Set_Id
		,Publ.Publication_Designation AS [Standard]
		--,CASE WHEN sp.Set_Id IS NOT NULL THEN SC.Set_Title 
		--ELSE Publ.Publication_Designation END AS [Standard]
		--,Prod.Product_Type
    FROM 
        [PRES_DIM].[dim_sws_packages] P
    JOIN 
        [PRES_DIM].[dim_sws_packagepublications] PP ON P.packageid = PP.packageid
	JOIN			[PRES_DIM].[dim_publication_current] Publ
       ON			Trim(PP.uri) = Trim(Publ.publication_uri)
	 --  LEFT JOIN 
	 --  [PRES_DIM].[dim_sws_organisations] Org 
		--ON p.OrgSalesforceId = Org.SalesforceId
		--JOIN 
  --      [PRES_DIM].[dim_sws_orgusers] OrgUsers 
		--ON Org.id = OrgUsers.organisationid
		--LEFT  JOIN	[PRES_DIM].[DIM_SWS_PackageUsers] PU
		--ON	OrgUsers.UserID = PU.UserId
	--left JOIN	[PRES_DIM].Dim_SetPublication_Current sp
 --      ON			sp.Publication_Id=Publ.Publication_Id --30601
	   --left JOIN			[PRES_DIM].Dim_Set_Current SC 
    --   ON			SC.Set_Id=sp.Set_Id
	--JOIN	[PRES_DIM].Dim_Product_Current Prod
 --      ON	Publ.Publication_Id = Prod.Product_Publication_Id
 --WHERE		Publ.Publication_Designation = 'AS 1926.1-2012' --43
),
FinalData AS (
    SELECT DISTINCT
        FO.UserID as [Customer_ID]
		,cast (concat('N_',FO.UserID) as varchar(50)) as [Customer_ID_All]
		,FO.MarketingCommunicationPref
		,FO.Primary_Contact_Title as [Customer_Job_Role]
		,FO.FirstName
		,FO.LastName
		,FO.AccountFullName as [Customer_Company_Name]
--		,FO.[Email included in Package] as [Email]
		,FO.[Org Email]
		,FO.Industry as [Customer_industry_sector]
		,FO.Customer_Company_Size
		--,PD.Set_Id
		,FO.TotalCustomerPrice as [Order_Product_Total_Cost]
		,FO.Order_Complete_Date
		,PD.Publication_Designation
		,pd.URI
		,PD.Standard
		,pd.Publication_Id
		,fo.Subscription_Status
--		,fo.[NUM_All Org User Email]
		,fo.[NUM_Active User Status]
		,fo.Purchase_Type
		,fo.Type
		
		
    FROM 
        FilteredOpportunities FO
    JOIN 
        PackageDetails PD ON FO.catlgsalesorderaccountkey = PD.catlgsalesorderaccountkey
    --where FO.[Email included in Package] is not null -- Not in Tiya's Query 
)
SELECT distinct FD.*,Prod.Product_Type -- Not in Tiya's Query 
FROM FinalData FD
	   JOIN			[PRES_DIM].Dim_Product_Current Prod
       ON			FD.Publication_Id = Prod.Product_Publication_Id
	   -- WHERE		FD.Publication_Designation = 'AS 1926.1-2012'
	   
	   where FD.Publication_Id in (117674,117675)
	   
	   where fd.URI in 
	   ('04-2733143442',
'04-1747491079',
'04-1211503873',
'04-3721604007',
'04-3744638727',
'04-2388465133',
'04-6859742350',
'04-1305884090',
'04-3938885690',
'04-2152763975',
'04-4214676603',
'04-1022506722',
'04-2000102465',
'04-3502342310',
'04-2723812457',
'04-1601638833',
'04-4085345746',
'04-2846804510',
'04-3828185382',
'04-1031474438',
'04-2101321809',
'04-3713831322',
'04-2604409428',
'04-3237535197',
'04-3075180020',
'04-2642364984',
'04-1626452480',
'04-3800469118',
'04-1818507249',
'04-2156631899',
'04-4067456120',
'04-3443945590',
'04-1685178556',
'04-1847104836',
'04-3949128371',
'04-2389888147',
'04-2032609399',
'04-2296712957',
'04-2582404860',
'04-3221644070',
'04-2225914130',
'04-1785906673',
'04-8571698230',
'04-5908949060',
'04-2593474022',
'04-4517857430',
'04-4187304480',
'04-5204335380',
'04-1465428531',
'04-2733143442',
'04-2191578359')

