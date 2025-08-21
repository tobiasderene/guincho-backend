
from sqlalchemy import Column, Integer, String, Date, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from app.db.database import Base

class MarcaVehiculo(Base):
    __tablename__ = 'marcas_vehiculos'

    id_marca_vehiculo = Column(Integer, primary_key=True)
    nombre_marca_vehiculo = Column(String, nullable=False)

    publicacion = relationship("Publicacion", back_populates="marca_vehiculo")


class CategoriaVehiculo(Base):
    __tablename__ = 'categorias_vehiculos'

    id_categoria_vehiculo = Column(Integer, primary_key=True)
    nombre_categoria_vehiculo = Column(String, nullable=False)

    publicacion = relationship("Publicacion", back_populates="categoria_vehiculo")

class Usuario(Base):
    __tablename__ = 'usuarios'

    id_usuario = Column(Integer, primary_key=True)
    nombre_usuario = Column(String, nullable=False)
    password = Column(String, nullable=False)
    tipo_usuario = Column(String, nullable=False)

    publicaciones = relationship("Publicacion", back_populates="usuario")
    comentarios = relationship("Comentario", back_populates="usuario")
    likes = relationship("Like", back_populates="usuario")


class Publicacion(Base):
    __tablename__ = 'publicaciones'

    id_publicacion = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    descripcion = Column(String, nullable=False)
    fecha_publicacion = Column(Date, nullable=False)
    descripcion_corta = Column(String, nullable=False)
    titulo = Column(String, nullable=False)
    url = Column(String, nullable=True)
    year_vehiculo = Column(Integer, nullable = False)
    id_categoria_vehiculo =  Column(Integer, ForeignKey('categorias_vehiculos.id_categoria_vehiculo'),nullable=False)
    id_marca_vehiculo = Column(Integer, ForeignKey('marcas_vehiculos.id_marca_vehiculo'),nullable=False)
    detalle = Column(String, nullable= False)

    usuario = relationship("Usuario", back_populates="publicaciones")
    comentarios = relationship("Comentario", back_populates="publicacion")
    likes = relationship("Like", back_populates="publicacion")
    imagenes = relationship("Imagen", back_populates="publicacion")
    categoria_vehiculo = relationship("CategoriaVehiculo", back_populates="publicacion")
    marca_vehiculo = relationship("MarcaVehiculo", back_populates="publicacion")



class Comentario(Base):
    __tablename__ = 'comentarios'

    id_comentario = Column(Integer, primary_key=True)
    descripcion_comentario = Column(String, nullable=False)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    id_publicacion = Column(Integer, ForeignKey('publicaciones.id_publicacion'), nullable=False)

    usuario = relationship("Usuario", back_populates="comentarios")
    publicacion = relationship("Publicacion", back_populates="comentarios")
    likes = relationship("Like", back_populates="comentario")

    
class Like(Base):
    __tablename__ = 'likes'

    id_like = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    id_comentario = Column(Integer, ForeignKey('comentarios.id_comentario'), nullable=True)
    id_publicacion = Column(Integer, ForeignKey('publicaciones.id_publicacion'), nullable=True)

    usuario = relationship("Usuario", back_populates="likes")
    comentario = relationship("Comentario", back_populates="likes")
    publicacion = relationship("Publicacion", back_populates="likes")


class Imagen(Base):
    __tablename__ = 'imagenes'

    id_imagen = Column(Integer, primary_key=True)
    id_publicacion = Column(Integer, ForeignKey('publicaciones.id_publicacion'), nullable=False)
    imagen_portada = Column(LargeBinary, nullable=False)
    url_foto = Column(String, nullable=False)

    publicacion = relationship("Publicacion", back_populates="imagenes")
