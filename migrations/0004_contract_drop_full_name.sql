-- ЛР3, шаг contract: чтение и запись уже полностью переведены на
-- first_name/last_name, старая колонка больше не нужна.

ALTER TABLE customers ALTER COLUMN first_name SET NOT NULL;
ALTER TABLE customers DROP COLUMN full_name;
