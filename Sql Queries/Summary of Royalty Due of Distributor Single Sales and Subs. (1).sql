SELECT DocumentDate,
       FORMAT(SUM(INTERTEK_SS),'#,0.00') AS INTERTEK_SS,
	   SUM(SAIG) AS INTERTEK_Subs,
       SUM(ACCURIS_SS) AS ACCURIS_SS,
	   SUM(ACCURIS) AS ACCURIS_Subs,
	   SUM(JSA_SS) AS JSA_SS,
	   SUM(KSA_SS) AS KSA_SS,
	   SUM(HIA_SS) AS HIA_SS,
	   SUM(DIN_SS) AS DIN_SS,
	   --test
	   SUM(MBA) AS MBA_Subs,
	   SUM(Firemate) AS Firemate_Subs
	   --test
FROM (
    SELECT DocumentDate,
           SUM(CASE WHEN DistributorID = 'SAIG' THEN RoyaltyDue ELSE 0 END) AS SAIG,
           SUM(CASE WHEN DistributorID = 'ACCURIS' THEN RoyaltyDue ELSE 0 END) AS ACCURIS,
		   SUM(CASE WHEN DistributorID = 'MBA' THEN RoyaltyDue ELSE 0 END) AS MBA,
		   SUM(CASE WHEN DistributorID = 'FireMate' THEN RoyaltyDue ELSE 0 END) AS Firemate,
           0 AS INTERTEK_SS,
           0 AS ACCURIS_SS,
		   0 AS JSA_SS,
		   0 AS KSA_SS,
		   0 AS HIA_SS,
		   0 AS DIN_SS
    FROM [PRES_DRR].Subscriptions_Summary
    WHERE ETL_ROW_CURRENT_FLAG = 1 AND ETL_ROW_DELETED_FLAG = 0 
	--and DOCUMENTDATE between '2023-07-01' and '2024-06-30'
    GROUP BY DOCUMENTDATE

    UNION ALL

    SELECT DocumentDate,
           0 AS SAIG,
           0 AS ACCURIS,
		   0 AS MBA,
		   0 AS Firemate,
		   
           SUM(CASE WHEN DistributorID = 'SAIG' THEN RoyaltyDue ELSE 0 END) AS INTERTEK_SS,
           SUM(CASE WHEN DistributorID = 'ACCURIS' THEN RoyaltyDue ELSE 0 END) AS ACCURIS_SS,
		   SUM(CASE WHEN DistributorID = 'JSA' THEN RoyaltyDue ELSE 0 END) AS JSA_SS,
		   SUM(CASE WHEN DistributorID = 'KSA' THEN RoyaltyDue ELSE 0 END) AS KSA_SS,
		   SUM(CASE WHEN DistributorID = 'HIA' THEN RoyaltyDue ELSE 0 END) AS HIA_SS,
		   SUM(CASE WHEN DistributorID = 'DIN' THEN RoyaltyDue ELSE 0 END) AS DIN_SS
    FROM [PRES_DRR].Single_Sales
    WHERE ETL_ROW_CURRENT_FLAG = 1 AND ETL_ROW_DELETED_FLAG = 0 
	--and DOCUMENTDATE between '2023-07-01' and '2024-06-30'
    GROUP BY DOCUMENTDATE
) AS CombinedResults
GROUP BY DocumentDate
ORDER BY DocumentDate desc;
