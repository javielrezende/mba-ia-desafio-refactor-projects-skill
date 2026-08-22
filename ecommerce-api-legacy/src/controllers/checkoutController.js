'use strict';

/** Orquestra: entrada já validada → service → resposta HTTP. Sem SQL, sem regra. */
function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            const { enrollmentId } = await checkoutService.checkout(req.validated);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };
