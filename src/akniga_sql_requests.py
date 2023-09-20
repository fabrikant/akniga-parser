def get_on_base_create_requests():
    req = []

    req.append("""
    DROP VIEW IF EXISTS books_view;
    """)

    req.append("""
    CREATE VIEW books_view AS
        SELECT books.title AS Название,
               authors.name AS Автор,
               books.duration AS [Продолжительность (мин)],
               books.free AS Бесплатная,
               performers.name AS Чтец,
               serias.name AS Серия,
               books.rating AS Рейтинг,
               books.year AS Год,
               books.description AS Описание,
               books.url
          FROM books
               LEFT JOIN
               authors ON books.author_id = authors.id
               LEFT JOIN
               performers ON books.performer_id = performers.id
               LEFT JOIN
               serias ON books.seria_id = serias.id;
    """)

    req.append("""
    DROP VIEW IF EXISTS books_filters_view;
    """)

    req.append("""
    CREATE VIEW books_filters_view AS
        SELECT books.title AS Название,
               authors.name AS Автор,
               books.duration AS [Продолжительность (мин)],
               books.free AS Бесплатная,
               performers.name AS Чтец,
               serias.name AS Серия,
               books.rating AS Рейтинг,
               books.year AS Год,
               filter_types.name AS [Тип Фильтра],
               filters.name AS Фильтр,
               books.description AS Описание,
               books.url
          FROM books
               LEFT JOIN
               authors ON books.author_id = authors.id
               LEFT JOIN
               performers ON books.performer_id = performers.id
               LEFT JOIN
               serias ON books.seria_id = serias.id
               LEFT JOIN
               books_filters ON books.id = books_filters.book_id
               LEFT JOIN
               filters ON books_filters.filter_id = filters.id
               JOIN
               filter_types ON filters.types_id = filter_types.id;
    """)

    req.append("""
    DROP VIEW IF EXISTS filters_view;
    """)

    req.append("""
    CREATE VIEW filters_view AS
        SELECT filter_types.name AS [Вид фильтра],
               parent.name AS Родитель,
               filters.name AS [Значение фильтра],
               filters.url
          FROM filters
               LEFT JOIN
               filter_types ON filters.types_id = filter_types.id
               LEFT JOIN
               filters AS parent ON parent.id = filters.parent_id
         ORDER BY filter_types.name,
                  filters.name;    
    """)

    return req