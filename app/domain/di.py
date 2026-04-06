from dishka import Provider, Scope, provide

from app.domain.interfaces.storages.movie import IMovieStorage
from app.domain.interfaces.storages.user import IUserStorage
from app.domain.uow import AbstractUow
from app.domain.use_cases.movie.create import CreateMovieUC
from app.domain.use_cases.movie.delete_by_id import DeleteMovieByIdUC
from app.domain.use_cases.movie.get_by_id import GetMovieByIdUC
from app.domain.use_cases.movie.get_list import GetMovieListUC
from app.domain.use_cases.movie.update_by_id import UpdateMovieByIdUC
from app.domain.use_cases.user.create import CreateUserUC
from app.domain.use_cases.user.delete_by_id import DeleteUserByIdUC
from app.domain.use_cases.user.get_by_id import GetUserByIdUC
from app.domain.use_cases.user.get_list import GetUserListUC
from app.domain.use_cases.user.update_by_id import UpdateUserByIdUC


class DomainProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def create_user(
        self,
        user_storage: IUserStorage,
        uow: AbstractUow,
    ) -> CreateUserUC:
        return CreateUserUC(
            user_storage=user_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def get_user_by_id(
        self,
        user_storage: IUserStorage,
        uow: AbstractUow,
    ) -> GetUserByIdUC:
        return GetUserByIdUC(
            user_storage=user_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def get_user_list(
        self,
        user_storage: IUserStorage,
        uow: AbstractUow,
    ) -> GetUserListUC:
        return GetUserListUC(
            user_storage=user_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def update_user_by_id(
        self,
        user_storage: IUserStorage,
        uow: AbstractUow,
    ) -> UpdateUserByIdUC:
        return UpdateUserByIdUC(
            user_storage=user_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def delete_user_by_id(
        self,
        user_storage: IUserStorage,
        uow: AbstractUow,
    ) -> DeleteUserByIdUC:
        return DeleteUserByIdUC(
            user_storage=user_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def create_movie(
        self,
        movie_storage: IMovieStorage,
        uow: AbstractUow,
    ) -> CreateMovieUC:
        return CreateMovieUC(
            movie_storage=movie_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def get_movie_by_id(
        self,
        movie_storage: IMovieStorage,
        uow: AbstractUow,
    ) -> GetMovieByIdUC:
        return GetMovieByIdUC(
            movie_storage=movie_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def get_movie_list(
        self,
        movie_storage: IMovieStorage,
        uow: AbstractUow,
    ) -> GetMovieListUC:
        return GetMovieListUC(
            movie_storage=movie_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def update_movie_by_id(
        self,
        movie_storage: IMovieStorage,
        uow: AbstractUow,
    ) -> UpdateMovieByIdUC:
        return UpdateMovieByIdUC(
            movie_storage=movie_storage,
            uow=uow,
        )

    @provide(scope=Scope.REQUEST)
    def delete_movie_by_id(
        self,
        movie_storage: IMovieStorage,
        uow: AbstractUow,
    ) -> DeleteMovieByIdUC:
        return DeleteMovieByIdUC(
            movie_storage=movie_storage,
            uow=uow,
        )
