extern crate protobuf;
use std::io::{Error, ErrorKind};
use protobuf::{Message};
use crate::gym_ferry::{GymnasiumMessage, StepReturn, ResetArgs, ResetReturn};
use crate::core::Communicator;
use std::collections::HashMap;

pub trait GymEnvironment {
    fn reset(&mut self, seed: Option<i32>, options: HashMap<String, String>) -> Result<(Vec<f32>, HashMap<String, String>), Error>;
    fn step(&mut self, action: Vec<f32>) -> Result<(Vec<f32>, f32, bool, bool, HashMap<String, String>), Error>;
    fn close(&mut self) -> Result<(), Error>;
}

struct ClientBackend<T: GymEnvironment> {
    env: T,
    communicator: Communicator,
}

impl<T: GymEnvironment> ClientBackend<T> {
    fn new(env: T, communicator: Communicator) -> ClientBackend<T> {
        ClientBackend { env, communicator }
    }

    fn run(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        loop {
            let mut message = GymnasiumMessage::new();
            message.set_request(true);
            self.communicator.send_message(&message)?;

            let response = self.communicator.receive_message()?;
            if response.has_action() {
                let action = decode(response.get_action());
                let (obs, reward, terminated, truncated, info) = self.env.step(action)?;
                let msg = create_step_return_message((obs, reward, terminated, truncated, info))?;
                self.communicator.send_message(&msg)?;
            } else if response.has_reset_args() {
                let seed = if response.get_reset_args().get_seed() != -1 { Some(response.get_reset_args().get_seed()) } else { None };
                let options = unwrap_dict(response.get_reset_args().get_options());
                let (obs, info) = self.env.reset(seed, options)?;
                let msg = create_reset_return_message((obs, info))?;
                self.communicator.send_message(&msg)?;
            } else if response.get_close() {
                self.env.close()?;
                break;
            } else {
                // Raise error
            }
            self.communicator.receive_message()?; // Dummy
        }
        Ok(())
    }
}

struct ServerBackend<T: GymEnvironment> {
    env: T,
    communicator: Communicator,
}

impl<T: GymEnvironment> ServerBackend<T> {
    fn new(env: T, communicator: Communicator) -> ServerBackend<T> {
        ServerBackend { env, communicator }
    }

    fn process_reset(&mut self, msg: &GymnasiumMessage) -> Result<(), Box<dyn std::error::Error>> {
        let reset_args = msg.get_reset_args();
        let seed = if reset_args.get_seed() != -1 { Some(reset_args.get_seed()) } else { None };
        let options = unwrap_dict(reset_args.get_options());
        let (obs, info) = self.env.reset(seed, options)?;
        let response = create_reset_return_message((obs, info))?;
        self.communicator.send_message(&response)?;
        Ok(())
    }

    fn process_close(&mut self, msg: &GymnasiumMessage) -> Result<(), Box<dyn std::error::Error>> {
        self.env.close()?;
        self.communicator.close()?;
        Ok(())
    }

    fn process_step(&mut self, msg: &GymnasiumMessage) -> Result<(), Box<dyn std::error::Error>> {
        let action = decode(msg.get_action());
        let (obs, reward, terminated, truncated, info) = self.env.step(action)?;
        let response = create_step_return_message((obs, reward, terminated, truncated, info))?;
        self.communicator.send_message(&response)?;
        Ok(())
    }

    fn run(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        loop {
            let msg = self.communicator.receive_message()?;
            if msg.has_action() {
                self.process_step(&msg)?;
            } else if msg.has_reset_args() {
                self.process_reset(&msg)?;
            } else if msg.get_close() {
                self.process_close(&msg)?;
                break;
            }
        }
        Ok(())
    }
}

// Decodes a Vec<f32> from a protobuf float list
fn decode(pb_float_list: &protobuf::RepeatedField<f32>) -> Vec<f32> {
    pb_float_list.into_iter().cloned().collect()
}

// Unwraps a protobuf Dict into a Rust HashMap
fn unwrap_dict(pb_dict: &Dict) -> HashMap<String, String> {
    let mut map = HashMap::new();
    for (k, v) in pb_dict.get_items().iter() {
        map.insert(k.to_string(), v.to_string());
    }
    map
}



fn create_step_return_message(step_return: (Vec<f32>, f32, bool, bool, HashMap<String, String>)) -> Result<GymnasiumMessage, Box<dyn std::error::Error>> {
    let (obs, reward, terminated, truncated, info) = step_return;
    let mut step_return_msg = StepReturn::new();
    step_return_msg.set_obs(RepeatedField::from_vec(obs));
    step_return_msg.set_reward(reward);
    step_return_msg.set_terminated(terminated);
    step_return_msg.set_truncated(truncated);
    // step_return_msg.set_info(wrap_dict(info)?);  // Need to implement wrap_dict

    let mut gym_message = GymnasiumMessage::new();
    gym_message.set_step_return(step_return_msg);
    Ok(gym_message)
}

fn create_reset_return_message(reset_return: (Vec<f32>, HashMap<String, String>)) -> Result<GymnasiumMessage, Box<dyn std::error::Error>> {
    let (obs, info) = reset_return;
    let mut reset_return_msg = ResetReturn::new();
    reset_return_msg.set_obs(RepeatedField::from_vec(obs));
    // reset_return_msg.set_info(wrap_dict(info)?);  // Need to implement wrap_dict

    let mut gym_message = GymnasiumMessage::new();
    gym_message.set_reset_return(reset_return_msg);
    Ok(gym_message)
}

fn create_reset_args_message(reset_args: (i32, HashMap<String, String>)) -> Result<GymnasiumMessage, Box<dyn std::error::Error>> {
    let (seed, options) = reset_args;
    let mut reset_args_msg = ResetArgs::new();
    reset_args_msg.set_seed(seed);
    // reset_args_msg.set_options(wrap_dict(options)?);  // Need to implement wrap_dict

    let mut gym_message = GymnasiumMessage::new();
    gym_message.set_reset_args(reset_args_msg);
    Ok(gym_message)
}

fn create_action_message(action: Vec<f32>) -> GymnasiumMessage {
    let mut gym_message = GymnasiumMessage::new();
    // gym_message.set_action(RepeatedField::from_vec(action));
    gym_message
}

fn create_close_message(close: bool) -> GymnasiumMessage {
    let mut gym_message = GymnasiumMessage::new();
    gym_message.set_close(close);
    gym_message
}
