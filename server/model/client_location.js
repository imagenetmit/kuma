const { BeanModel } = require("redbean-node/dist/bean-model");
const { R } = require("redbean-node");

/**
 * ClientLocation model
 */
class ClientLocation extends BeanModel {
    /**
     * Return an object that is ready to be converted to JSON
     * @returns {object} Object ready to be converted to JSON
     */
    async toJSON() {
        let client = null;
        
        if (this.client_id) {
            const clientBean = await R.findOne("client", " id = ? ", [this.client_id]);
            if (clientBean) {
                client = {
                    id: clientBean.id,
                    name: clientBean.name
                };
            }
        }
        
        return {
            id: this.id,
            name: this.name,
            description: this.description,
            address: this.address,
            city: this.city,
            state: this.state,
            zip: this.zip,
            country: this.country,
            clientId: this.client_id,
            client: client,
            active: Boolean(this.active),
        };
    }
}

module.exports = ClientLocation; 