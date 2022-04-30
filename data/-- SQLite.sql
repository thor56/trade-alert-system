-- SQLite
SELECT
    T1.*,
    DerivedTable.swings
FROM TradeCall T1
JOIN
(
    SELECT 
        T2.*,
        ROW_NUMBER() OVER (PARTITION BY T2.SymbolDb ORDER BY datetime(T2.time_close) DESC) AS RowNum,
        CASE
        WHEN T2.swings < 0  THEN T2.price_low 
        ELSE T2.price_high
        END 
    FROM SwingTable T2, TradeCall T1
    WHERE datetime(T2.time_close) < datetime(T1.TimeStamp)
    AND T2.swings IS NOT NULL AND
    CASE
    WHEN T1.Position = 'LONG' THEN T2.swings < 0
    ELSE T2.swings > 0
END
) DerivedTable
ON T1.Ticker = DerivedTable.SymbolDb
WHERE DerivedTable.RowNum = 1