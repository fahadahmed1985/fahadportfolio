
select count(1) FROM [STG_REC].[Exp_Recommendations_4WebUI_V_FB] -- 1,400,959

select count(1) FROM [STG_REC].[HRE_Recommendations_4WebUI_V] -- 5,007,021

select top 10000 * FROM [STG_REC].[Exp_Recommendations_4WebUI_V_FB]


SELECT  std_exp.[URI]
      ,std_exp.[Designation]
      ,std_exp.[Related Designation]
      ,std_exp.[Score] as [original_score_std]
	  ,std_exp.[Score]*0.5 as [weighted_score_std]
	  ,std_hre.URI
	   ,std_hre.Score as [original_score_hre]
	  ,std_hre.Score *0.5 as [weighted_score_hre]
      ,(std_exp.[Score]*0.5 ) + (std_hre.Score *0.5) AS [Final_Score]

FROM [STG_REC].[Exp_Recommendations_4WebUI_V_FB] std_exp
    inner join [STG_REC].[HRE_Recommendations_4WebUI_V] std_hre
	on std_exp.[URI] = std_hre.URI


