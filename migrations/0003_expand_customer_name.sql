-- ЛР3, шаг expand: разбиваем full_name на first_name/last_name без простоя.
-- Старая колонка пока остаётся и становится необязательной, чтобы во время
-- перехода работали обе версии приложения: старая ещё пишет full_name,
-- новая уже пишет first_name/last_name.

ALTER TABLE customers ADD COLUMN first_name VARCHAR(255);
ALTER TABLE customers ADD COLUMN last_name VARCHAR(255);

UPDATE customers
SET first_name = split_part(full_name, ' ', 1),
    last_name = CASE
        WHEN position(' ' in full_name) > 0
            THEN NULLIF(substring(full_name from position(' ' in full_name) + 1), '')
        ELSE NULL
    END
WHERE full_name IS NOT NULL;

ALTER TABLE customers ALTER COLUMN full_name DROP NOT NULL;
