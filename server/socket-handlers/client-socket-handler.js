const { checkLogin } = require("../util-server");
const { R } = require("redbean-node");
const { log } = require("../../src/util");

/**
 * Handlers for client and location related events
 * @param {Socket} socket Socket.io instance
 * @returns {void}
 */
module.exports.clientSocketHandler = (socket) => {
    // Get list of clients
    socket.on("getClients", async (callback) => {
        try {
            checkLogin(socket);
            const list = await R.find("clients", " 1=1 ");
            const result = list.map(client => ({
                id: client.id,
                name: client.name,
                description: client.description
            }));
            callback({
                ok: true,
                clients: result
            });
        } catch (error) {
            log.error("getClients", error);
            callback({
                ok: false,
                msg: error.message
            });
        }
    });

    // Get list of locations
    socket.on("getLocations", async (callback) => {
        try {
            checkLogin(socket);
            const list = await R.find("client_location", " 1=1 ");
            const result = list.map(location => ({
                id: location.id,
                name: location.name,
                description: location.description,
                address: location.address,
                clientId: location.client_id
            }));
            callback({
                ok: true,
                locations: result
            });
        } catch (error) {
            log.error("getLocations", error);
            callback({
                ok: false,
                msg: error.message
            });
        }
    });
}; 