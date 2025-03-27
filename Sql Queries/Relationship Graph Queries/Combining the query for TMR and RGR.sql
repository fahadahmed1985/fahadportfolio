-- Combined Query and steps 

--Original RG 

select top 10 *  FROM [STG_DIM].[RG_Recommendations]

--Original TM 

select top 10 *  FROM [STG_DIM].[TM_Recommendations]


--Get Explicit data 

--FROM		[STG_REC].[Std_Explicit_Relations_V_FB] 
--into [STG_REC].[Exp_Recommendations_4WebUI_V_FB]

-- Combining both table 

select URI,URI_recomm,Recomm_Score, CAST(Recomm_Score AS float) * 0.3 AS Updated_Score,'RGR' AS [Type]-- into[STG_REC].TEMP_COMB_TMR_RGR_FB
FROM [STG_DIM].[RG_Recommendations] -- 617,277
--where URI = '00-3644540841'
union all -- 5,305,668
select  URI,URI_recomm,Recomm_Score, CAST(Recomm_Score AS float) * 0.7 AS Updated_Score,'TMR' AS [Type] FROM [STG_DIM].[TM_Recommendations] -- 4,604,629
--where URI = '00-3644540841'
order by 1,2,3

-- Grouping by summing the score  [STG_REC].TEMP_COMB_TMR_RGR_FB

select  URI,URI_recomm,sum(Updated_Score) as [Total Score]-- into [STG_REC].TEMP_COMB_RGR_TMR_Webview_FB 
 from [STG_REC].TEMP_COMB_TMR_RGR_FB --5,102,400
 --where URI = '00-1002392024'
--where Designation = 'ISO 3696:1987'  --and [Related Designation] = 'ISO 3696:1987'
Group by URI, URI_recomm
order by URI_recomm

-- Final Query for Power BI 

select rg.URI, st.DESIGNATION as [Org.Designation], rg.[URI_recomm] as URI_recomm,relst.DESIGNATION as [Rel.Standard] ,rg.[Total Score] as Recomm_Score  --Recomm_Score  --617277
FROM [STG_REC].TEMP_COMB_RGR_TMR_Webview_FB  rg --5,102,400
left join PRES_DIM.Dim_Standard_Current st
on st.URI = rg.URI
left join PRES_DIM.Dim_Standard_Current relst
on relst.URI = rg.[URI_recomm]
--where rg.URI ='00-1002392024'
--where rg.ETL_ROW_CURRENT_FLAG = 1 and rg.ETL_ROW_DELETED_FLAG =0 
Group by rg.URI,rg.[URI_recomm],st.DESIGNATION,relst.DESIGNATION,rg.[Total Score]  Having RG.URI <> rg.[URI_recomm]
order by rg.[Total Score] desc,rg.[URI_recomm],URI