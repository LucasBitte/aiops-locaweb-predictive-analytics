{{ config(materialized='table') }}

SELECT DISTINCT
    -- Surrogate key robusta com delimitadores para evitar colisões de hash
    MD5(COALESCE("Produto", '') || '||' || COALESCE("Categoria", '') || '||' || COALESCE("Subcategoria", '')) AS dim_produto_categoria_sk,

    -- Atributos do ativo de TI e natureza da falha
    "Produto"                                           AS produto,
    "Categoria"                                         AS categoria,
    "Subcategoria"                                      AS subcategoria

FROM {{ ref('stg_incidents') }}