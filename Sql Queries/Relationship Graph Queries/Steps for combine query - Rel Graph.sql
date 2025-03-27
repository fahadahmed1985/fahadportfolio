-- Combined Query and steps 

--Original HRE Table/view 

select top 10 * from [STG_REC].[HRE_Recommendations_V]

--Final Table used in HPE HRE Table/view 

[STG_REC].[HRE_Recommendations_4WebUI_V_FB]

--Get Explicit data 

--FROM		[PRES_DIM].[Dim_Standard_Relationships_Current]
--into [STG_REC].[Exp_Recommendations_4WebUI_V_FB]

-- Combining both table 

select PARENT_URI as [URI], CHILD_URI as [Related URI] , 0.5 AS Half_Score,'EXP' AS [Type] --into [STG_REC].TEMP_COMB_EXP_HRE_FB
FROM [PRES_DIM].[Dim_Standard_Relationships_Current] --  AFter Filter:1,401,219 OLD: 1,744,592
where CHILD_URI is not null-- PARENT_URI = '04-1374550391'
union all --After filter: 6,503,076 OLD: 6,846,449
select  URI, [URI_recomm], [Total Score] / 2 AS Half_Score , 'HRE' AS [Type] FROM [STG_REC].TEMP_COMB_RGR_TMR_Webview_FB --5,101,857--old one: [STG_REC].[HRE_Recommendations_4WebUI_V_FB] -- 5,007,021
--where   URI = '00-1002392024'
order by 1,2,3

-- Grouping by summing the score  [STG_REC].TEMP_COMB_EXP_HRE_FB

select  URI, [Related URI] ,sum(Half_Score) as [Total Score]-- into [STG_REC].TEMP_COMB_EXP_HRE_Webview_FB 
 from [STG_REC].TEMP_COMB_EXP_HRE_FB --5,996,049
--where Designation = 'ISO 3696:1987'  --and [Related Designation] = 'ISO 3696:1987'
Group by URI, [Related URI]
order by [Total Score] desc ,[Related URI]

-- Final Query for Power BI 

select rg.URI, st.DESIGNATION as [Org.Designation], rg.[Related URI] as URI_recomm,relst.DESIGNATION as [Rel.Standard] ,rg.[Total Score] as Recomm_Score  --Recomm_Score  --5,960,519
FROM [STG_REC].[TEMP_COMB_EXP_HRE_Webview_FB] rg
left join PRES_DIM.Dim_Standard_Current st
on st.URI = rg.URI
left join PRES_DIM.Dim_Standard_Current relst
on relst.URI = rg.[Related URI]
--where rg.URI ='00-1002392024'
--where rg.ETL_ROW_CURRENT_FLAG = 1 and rg.ETL_ROW_DELETED_FLAG =0 
Group by rg.URI,rg.[Related URI],st.DESIGNATION,relst.DESIGNATION,rg.[Total Score]  Having RG.URI <> rg.[Related URI]
order by rg.[Related URI],URI