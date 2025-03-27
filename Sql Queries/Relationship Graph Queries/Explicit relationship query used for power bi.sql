

select rg.Parent_URI, st.DESIGNATION as [Org.Designation], rg.CHILD_URI,relst.DESIGNATION as [Rel.Standard] ,1 as Recomm_Score  --Recomm_Score  --1,365,689
FROM [PRES_DIM].[Dim_Standard_Relationships_Current] rg -- This is the table coming from SIM Searchable work done by Altis
left join PRES_DIM.Dim_Standard_Current st
on st.URI = rg.Parent_URI
left join PRES_DIM.Dim_Standard_Current relst
on relst.URI = rg.CHILD_URI
where rg.ETL_ROW_CURRENT_FLAG = 1 and rg.ETL_ROW_DELETED_FLAG =0 
Group by rg.Parent_URI,rg.CHILD_URI,st.DESIGNATION,relst.DESIGNATION  Having RG.Parent_URI <> RG.CHILD_URI
order by CHILD_URI,Parent_URI