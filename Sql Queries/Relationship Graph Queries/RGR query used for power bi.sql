

select rg.URI, st.DESIGNATION as [Org.Designation], rg.URI_recomm,relst.DESIGNATION as [Rel.Standard] ,rg.Recomm_Score  --Recomm_Score  --617277
FROM [STG_DIM].[RG_Recommendations] rg -- This is a view which is fetching from stg REC RG  table 
left join PRES_DIM.Dim_Standard_Current st
on st.URI = rg.URI
left join PRES_DIM.Dim_Standard_Current relst
on relst.URI = rg.URI_recomm
where rg.ETL_ROW_CURRENT_FLAG = 1 and rg.ETL_ROW_DELETED_FLAG =0 
Group by rg.URI,rg.URI_recomm,st.DESIGNATION,relst.DESIGNATION,rg.Recomm_Score  Having RG.URI <> RG.URI_recomm
order by URI_recomm,URI