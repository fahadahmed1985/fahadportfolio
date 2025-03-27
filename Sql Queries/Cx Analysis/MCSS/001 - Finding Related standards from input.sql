DECLARE @Designations TABLE (Designation VARCHAR(200));

-- Insert the designations you want as input values
INSERT INTO @Designations (Designation)
VALUES 

('AS/NZS 3000:2018'),
('AS 1428.1:2021'),
('AS 1684.2:2021'),
('AS/NZS 5033:2021'),
('AS/NZS 6400:2016'),
('AS 5369:2023'),
('AS ISO 31000:2018'),
('AS 3740:2021'),
('AS 1288:2021'),
('AS/NZS ISO 9001:2016'),
('AS/NZS ISO 45001:2018'),
('AS 4811:2022'),
('AS/NZS 3760:2022'),
('AS 8001:2021'),
('ISO 9001:2015');


-- Main query
SELECT 
    rg.URI,
    s.designation,
    rg.[Related URI] AS URI_recomm,
    srg.designation,
    rg.[Total Score] AS Recomm_Score  
FROM [STG_REC].[TEMP_COMB_EXP_HRE_Webview_FB] rg
JOIN [Mrkt_Dim].[Standard] s 
    ON s.uri = rg.URI
JOIN [Mrkt_Dim].[Standard] srg 
    ON srg.uri = rg.[Related URI]
WHERE rg.[Total Score] <> 0
AND rg.URI <> rg.[Related URI] 
AND s.designation IN (SELECT Designation FROM @Designations)
ORDER BY rg.[Total Score] DESC;


