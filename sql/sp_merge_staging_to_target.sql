DROP PROCEDURE IF EXISTS public.merge_staging_to_target(
    TEXT,
    TEXT,
    TEXT
);

CREATE OR REPLACE PROCEDURE public.merge_staging_to_target(
    p_table_name  TEXT,
    p_schema_name TEXT DEFAULT 'public'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_stg_table_name TEXT;

    -- PK 컬럼 목록
    v_key_columns TEXT[];

    -- MERGE 구문 구성 요소
    v_join_condition TEXT;
    v_update_columns TEXT;
    v_insert_columns TEXT;
    v_insert_values  TEXT;
    v_sql            TEXT;
BEGIN
    v_stg_table_name := 'stg_' || p_table_name;

    /*
     * 타겟 테이블의 Primary Key 컬럼 조회
     * 복합 PK인 경우 PK 정의 순서대로 배열에 저장
     */
    SELECT array_agg(a.attname ORDER BY k.ordinality)
      INTO v_key_columns
      FROM pg_catalog.pg_constraint c
      JOIN pg_catalog.pg_class t
        ON t.oid = c.conrelid
      JOIN pg_catalog.pg_namespace n
        ON n.oid = t.relnamespace
      CROSS JOIN LATERAL
           unnest(c.conkey) WITH ORDINALITY AS k(attnum, ordinality)
      JOIN pg_catalog.pg_attribute a
        ON a.attrelid = t.oid
       AND a.attnum = k.attnum
     WHERE c.contype = 'p'
       AND n.nspname = p_schema_name
       AND t.relname = p_table_name;

    IF v_key_columns IS NULL
       OR cardinality(v_key_columns) = 0 THEN
        RAISE EXCEPTION
            'Primary Key가 존재하지 않습니다: %.%',
            p_schema_name,
            p_table_name;
    END IF;

    /*
     * 예:
     * 단일 PK  → t.id = s.id
     * 복합 PK  → t.company_id = s.company_id
     *            AND t.product_id = s.product_id
     */
    SELECT string_agg(
               format('t.%I = s.%I', key_column, key_column),
               ' AND '
           )
      INTO v_join_condition
      FROM unnest(v_key_columns) AS key_column;

    /*
     * UPDATE 대상 컬럼 생성
     * Primary Key 컬럼은 UPDATE 대상에서 제외
     */
    SELECT string_agg(
               format('%I = s.%I', column_name, column_name),
               ', ' ORDER BY ordinal_position
           )
      INTO v_update_columns
      FROM information_schema.columns
     WHERE table_schema = p_schema_name
       AND table_name = p_table_name
       AND column_name <> ALL(v_key_columns);

    /*
     * INSERT 대상 컬럼과 값 생성
     */
    SELECT string_agg(
               format('%I', column_name),
               ', ' ORDER BY ordinal_position
           ),
           string_agg(
               format('s.%I', column_name),
               ', ' ORDER BY ordinal_position
           )
      INTO v_insert_columns,
           v_insert_values
      FROM information_schema.columns
     WHERE table_schema = p_schema_name
       AND table_name = p_table_name;

    IF v_insert_columns IS NULL THEN
        RAISE EXCEPTION
            '타겟 테이블이 존재하지 않거나 컬럼이 없습니다: %.%',
            p_schema_name,
            p_table_name;
    END IF;

    /*
     * PK 이외의 컬럼이 있을 때만 UPDATE 구문 생성
     */
    IF v_update_columns IS NOT NULL THEN
        v_sql := format(
            $merge$
            MERGE INTO %I.%I AS t
            USING %I.%I AS s
               ON %s
            WHEN MATCHED THEN
                UPDATE SET %s
            WHEN NOT MATCHED THEN
                INSERT (%s)
                VALUES (%s)
            $merge$,
            p_schema_name,
            p_table_name,
            p_schema_name,
            v_stg_table_name,
            v_join_condition,
            v_update_columns,
            v_insert_columns,
            v_insert_values
        );
    ELSE
        /*
         * 테이블에 PK 컬럼만 있는 경우에는
         * UPDATE SET에 넣을 컬럼이 없으므로 INSERT만 수행
         */
        v_sql := format(
            $merge$
            MERGE INTO %I.%I AS t
            USING %I.%I AS s
               ON %s
            WHEN NOT MATCHED THEN
                INSERT (%s)
                VALUES (%s)
            $merge$,
            p_schema_name,
            p_table_name,
            p_schema_name,
            v_stg_table_name,
            v_join_condition,
            v_insert_columns,
            v_insert_values
        );
    END IF;

    EXECUTE v_sql;

    EXECUTE format(
        'TRUNCATE TABLE %I.%I',
        p_schema_name,
        v_stg_table_name
    );
END;
$$;