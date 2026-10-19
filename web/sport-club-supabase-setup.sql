-- ============================================================
-- SPORT CLUB · THAYS — Setup de base de datos en Supabase
-- Ejecutar en: supabase.com → SQL Editor → New query
-- ============================================================

-- Tabla de ejercicios
CREATE TABLE exercise_logs (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  date        DATE NOT NULL DEFAULT CURRENT_DATE,
  exercise_name TEXT NOT NULL,
  sets        INTEGER,
  reps        INTEGER,
  weight_kg   NUMERIC(6,2),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de peso corporal
CREATE TABLE body_weight_logs (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  date        DATE NOT NULL DEFAULT CURRENT_DATE,
  weight_kg   NUMERIC(5,2) NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, date)  -- Un registro por día
);

-- Seguridad: cada usuario solo ve sus propios datos
ALTER TABLE exercise_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Solo datos propios" ON exercise_logs
  FOR ALL USING (auth.uid() = user_id);

ALTER TABLE body_weight_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Solo datos propios" ON body_weight_logs
  FOR ALL USING (auth.uid() = user_id);

-- Índices para búsquedas rápidas
CREATE INDEX ON exercise_logs (user_id, date);
CREATE INDEX ON body_weight_logs (user_id, date);
