create table facultad (
    idfacultad serial not null,
    nomfacultad varchar(100) not null,
    primary key (idfacultad)
);

create table escuela (
    idescuela serial not null,
    nomescuela varchar(100) not null,
    idfacultad int not null,
    primary key (idescuela)
);

create table plan_estudio (
    idplanestudio serial not null,
    idescuela int not null,
    nombre varchar(5) not null,
    version char(1) not null,
    primary key (idplanestudio)
);

create table curso (
    idcurso serial not null,
    codcurso varchar(20) not null,
    nomcurso varchar(100) not null,
    creditos int not null,
    h_teorica int not null,
    h_practica int not null,
    tipo_curso boolean not null,
    dificultad smallint null,
    primary key (idcurso)
);

create table curso_curso (
    cursoid int not null,
    curso_prereqid int not null,
    primary key(cursoid, curso_prereqid)
);

create table plan_curso (
    idplancurso serial not null,
    idplanestudio int not null,
    idcurso int not null,
    ciclo smallint not null,
    primary key (idplancurso)
);

create table semestre (
    idsemestre varchar(6) not null,
    fecha_inicio date not null,
    fecha_fin date not null,
    estado_semestre char(1) not null,
    primary key (idsemestre)
);

create table curso_programado (
    idcursoprog serial not null,
    promedfinal numeric(4, 2) not null,
    condicion char(1) not null,
    idsemestre varchar not null,
    idplancurso int not null,
    iddocente int not null,
    primary key (idcursoprog)
);
create table docente (
    iddocente serial not null,
    nombres varchar(40) not null,
    apepat varchar(40) not null,
    apemat varchar(40) not null,
    dni char(8) not null unique,
    correo varchar(50) not null unique,
    sexo char(1) not null,
    direccion varchar(100) not null,
    tipo_docente char(2) not null,
    grado_academico char(1) not null,
    estado_docente boolean not null,
    primary key (iddocente)
);

create table estudiante (
    idestudiante serial not null,
    idsemestreing varchar not null,
    idplanestudio int not null,
    nombres varchar(40) not null,
    apepat varchar(40) not null,
    apemat varchar(40) not null,
    dni char(8) not null unique,
    correo varchar(50) not null unique,
    sexo char(1) not null,
    fechanac date not null,
    direccion varchar(100) not null,
    estadoalu char(1) not null,
    primary key (idestudiante)
);

create table matricula (
    idmatricula serial not null,
    idestudiante int not null,
    idsemestre varchar not null,
    fecha_matricula date not null,
    hora_matricula time not null,
    primary key (idmatricula)
);

create table detalle_matricula (
    iddetmat serial not null,
    idcursoprog int not null,
    idmatricula int not null,
    estado char(1) not null,
    nota_promedio numeric(4,2) not null,
    modalidad char(1) not null,
    primary key (iddetmat)
);

alter table curso_curso add constraint fk_curso_curo78457 foreign key (cursoid) references curso (idcurso);
alter table curso_curso add constraint fk_curso_curo47921 foreign key (curso_prereqid) references curso (idcurso);
alter table curso_programado add constraint fk_curso_prog306185 foreign key (idplancurso) references plan_curso (idplancurso);
alter table curso_programado add constraint fk_curso_prog771883 foreign key (iddocente) references docente (iddocente);
alter table curso_programado add constraint fk_curso_prog86576 foreign key (idsemestre) references semestre (idsemestre);
alter table detalle_matricula add constraint fk_detalle_ma382286 foreign key (idmatricula) references matricula (idmatricula);
alter table detalle_matricula add constraint fk_detalle_ma670241 foreign key (idcursoprog) references curso_programado (idcursoprog);
alter table escuela add constraint fk_escuela_746448 foreign key (idfacultad) references facultad (idfacultad);
alter table estudiante add constraint fk_estudiante581295 foreign key (idsemestreing) references semestre (idsemestre);
alter table estudiante add constraint fk_estudiante386415 foreign key (idplanestudio) references plan_estudio (idplanestudio);
alter table matricula add constraint fk_matricula648029 foreign key (idsemestre) references semestre (idsemestre);
alter table matricula add constraint fk_matricula994571 foreign key (idestudiante) references estudiante (idestudiante);
alter table plan_curso add constraint fk_plan_curso342191 foreign key (idcurso) references curso (idcurso);
alter table plan_curso add constraint fk_plan_curso433694 foreign key (idplanestudio) references plan_estudio (idplanestudio);
alter table plan_estudio add constraint fk_plan_estud144504 foreign key (idescuela) references escuela (idescuela);
