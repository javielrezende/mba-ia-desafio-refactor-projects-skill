'use strict';

function createUserController({ userService }) {
    return {
        async remove(req, res) {
            await userService.deleteUser(req.validated.id);
            res.status(200).send('Usuário deletado.');
        },
    };
}

module.exports = { createUserController };
