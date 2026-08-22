'use strict';

const { PaymentStatus } = require('../config/constants');
const { NotFoundError, PaymentDeclinedError } = require('../domain/errors');

/**
 * Regra de negócio do checkout. Não conhece Express: recebe dados já validados
 * e lança erro de domínio, que o error handler traduz em resposta HTTP.
 *
 * Todas as escritas acontecem em uma única transação — falha em qualquer passo
 * desfaz os anteriores, em vez de deixar matrícula sem pagamento (RP-09).
 */
function createCheckoutService({
    db,
    userRepository,
    courseRepository,
    enrollmentRepository,
    paymentRepository,
    auditLogRepository,
    paymentGateway,
    passwordHasher,
    logger,
}) {
    return {
        async checkout({ userName, email, password, courseId, cardNumber }) {
            const course = await courseRepository.findActiveById(courseId);
            if (!course) throw new NotFoundError('Curso não encontrado');

            const existingUser = await userRepository.findByEmail(email);

            return db.transaction(async (tx) => {
                const userId = existingUser
                    ? existingUser.id
                    : (
                          await userRepository.create(
                              {
                                  name: userName,
                                  email,
                                  passwordHash: await passwordHasher.hash(password),
                              },
                              tx,
                          )
                      ).id;

                const payment = await paymentGateway.charge({
                    cardNumber,
                    amount: course.price,
                });

                if (payment.status !== PaymentStatus.PAID) {
                    throw new PaymentDeclinedError();
                }

                const enrollment = await enrollmentRepository.create({ userId, courseId }, tx);

                await paymentRepository.create(
                    { enrollmentId: enrollment.id, amount: course.price, status: payment.status },
                    tx,
                );

                await auditLogRepository.create(
                    { action: `Checkout curso ${courseId} por ${userId}` },
                    tx,
                );

                logger.info(
                    { userId, courseId, enrollmentId: enrollment.id, course: course.title },
                    'checkout concluído',
                );

                return { enrollmentId: enrollment.id };
            });
        },
    };
}

module.exports = { createCheckoutService };
