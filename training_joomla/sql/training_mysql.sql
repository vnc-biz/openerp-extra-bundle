CREATE TABLE zik_training_offer_format (
    id int(11) unsigned NOT NULL,
    name varchar(100) NOT NULL DEFAULT '',
    alias varchar(100) NOT NULL DEFAULT '',
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_offer (
    id int(11) unsigned NOT NULL,
    description text,
    type_id integer,
    requeriments text,
    management text,
    notification_note text,
    format_id integer NOT NULL,
    kind character varying(16) NOT NULL,
    name character varying(64) NOT NULL,
    alias character varying(64) NOT NULL,
    metakey text,
    metadescription text,
    frontpage boolean,
    product_line_id integer NOT NULL,
    sequence integer,
    lang_id integer,
    objective text,
    target_public_id integer,
    product_id integer,
    is_certification boolean,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_course_theme (
    id int(11) unsigned NOT NULL,
    parent_id integer,
    name character varying(64) NOT NULL,
    alias varchar(100) NOT NULL DEFAULT '',
    description text,
    priority integer,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_course_theme_rel (
  course_id int(11) unsigned NOT NULL,
  theme_id int(11) unsigned NOT NULL
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_offer_theme_rel (
  offer_id int(11) unsigned NOT NULL,
  theme_id int(11) unsigned NOT NULL
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_included_offer_offer_rel (
    offer_id int(11) unsigned NOT NULL,
    included_offer_id int(11) unsigned NOT NULL
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_complementary_offer_offer_rel (
    offer_id int(11) unsigned NOT NULL,
    complementary_offer_id int(11) unsigned NOT NULL
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_offer_preliminary_offer_rel (
    offer_id int(11) unsigned NOT NULL,
    preliminary_offer_id int(11) unsigned NOT NULL
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_course_type (
    id int(11) unsigned NOT NULL,
    min_limit int(11) unsigned NOT NULL,
    max_limit int(11) unsigned NOT NULL,
    name varchar(100) NOT NULL DEFAULT '',
    alias varchar(100) NOT NULL DEFAULT '',
    objective text,
    description text,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_course (
    id int(11) unsigned NOT NULL,
    duration_without_children double precision,
    duration_with_children numeric(16,2),
    course_type_id integer,
    p_id integer,
    sequence integer,
    long_name character varying(256),
    alias character varying(256) NOT NULL,
    metakey text,
    metadescription text,
    reference_id integer,
    duration numeric(16,2),
    internal_note text,
    kind character varying(16) NOT NULL,
    has_support tinyint(1) NOT NULL DEFAULT '0',
    with_children tinyint(1) NOT NULL DEFAULT '0',
    state_course character varying(16) NOT NULL,
    lang_id int(11) unsigned NOT NULL,
    category_id integer,
    splitted_by character varying(16) NOT NULL,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_course_category (
    id int(11) unsigned NOT NULL,
    analytic_account_id integer,
    price_list_id integer,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_course_offer_rel(
    offer_id integer NOT NULL,
    course_id integer NOT NULL
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_session (
    id int(11) unsigned NOT NULL,
    address_id integer,
    date_end datetine NOT NULL,
    min_limit_reached tinyint(1) NOT NULL DEFAULT '0',
    date datetine NOT NULL,
    participant_count_manual integer,
    format_id int(11) unsigned NOT NULL,
    name character varying(64) NOT NULL,
    alias character varying(64) NOT NULL,
    metakey text,
    metadescription text,
    manual tinyint(1) NOT NULL DEFAULT '0',
    catalog_id integer,
    offer_id int(11) unsigned NOT NULL,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_images (
    id int(11) unsigned NOT NULL,
    name varchar(100) NOT NULL DEFAULT '',
    offer_id integer,
    comments text,
    filename character varying(250),
    base_image boolean,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_product_product (
    id int(11) unsigned NOT NULL,
    name varchar(128) NOT NULL DEFAULT '',
    list_price numeric(16,2),
    deposit_price numeric(16,2),
    default_code character varying(64),
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_res_partner (
    id int(11) unsigned NOT NULL,
    name varchar(128) NOT NULL DEFAULT '',
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_res_partner_address (
    id int(11) unsigned NOT NULL,
    function integer,
    fax character varying(64),
    street2 character varying(128),
    phone character varying(64),
    street character varying(128),
    active tinyint(1) NOT NULL DEFAULT '0',
    partner_id integer,
    city character varying(128),
    name character varying(64),
    zip character varying(24),
    title character varying(32),
    mobile character varying(64),
    country_id integer,
    birthdate character varying(64),
    state_id integer,
    type character varying(16),
    email character varying(240),
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_res_lang (
    id int(11) unsigned NOT NULL,
    code character varying(5) NOT NULL,
    name character varying(64) NOT NULL,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_images (
    id int(11) unsigned NOT NULL,
    name character varying(100) NOT NULL,
    offer_id integer,
    comments text,
    filename character varying(250),
    base_image boolean,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_res_country (
    id int(11) unsigned NOT NULL,
    code character varying(2) NOT NULL,
    name character varying(64) NOT NULL,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;

CREATE TABLE zik_training_offer_public_target(
    id int(11) unsigned NOT NULL,
    name character varying(256) NOT NULL,
    note text,
    changed tinyint(1) NOT NULL,
    PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8;
