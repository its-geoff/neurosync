`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 12/22/2025 12:28:57 PM
// Design Name: 
// Module Name: UART_TX
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module UART_TX
  #(parameter CLKS_PER_BIT = 868)  //100MHz / 115200 ≈ 868
  (
    input        i_Clock,
    input        i_TX_DV,       //1-cycle pulse to start sending i_TX_Byte
    input  [7:0] i_TX_Byte,
    output       o_TX_Active,   //high while transmitting
    output reg   o_TX_Serial,   //UART TX line
    output       o_TX_Done      //1-cycle pulse when done
  );

  //State Machine parameters
  parameter IDLE         = 3'b000;
  parameter TX_START_BIT = 3'b001;
  parameter TX_DATA_BITS = 3'b010;
  parameter TX_STOP_BIT  = 3'b011;
  parameter CLEANUP      = 3'b100;

  reg [2:0] r_SM_Main     = IDLE;
  reg [9:0] r_Clock_Count = 0;      //big enough for 868
  reg [2:0] r_Bit_Index   = 0;
  reg [7:0] r_TX_Data     = 0;

  reg r_TX_Active = 1'b0;
  reg r_TX_Done   = 1'b0;

  assign o_TX_Active = r_TX_Active;
  assign o_TX_Done   = r_TX_Done;

  always @(posedge i_Clock) begin
    r_TX_Done <= 1'b0; //default

    case (r_SM_Main)

      IDLE: begin
        o_TX_Serial   <= 1'b1; //line idle high
        r_TX_Active   <= 1'b0;
        r_Clock_Count <= 0;
        r_Bit_Index   <= 0;

        if (i_TX_DV == 1'b1) begin
          r_TX_Data   <= i_TX_Byte;   //latch data
          r_TX_Active <= 1'b1;
          r_SM_Main   <= TX_START_BIT;
        end else begin
          r_SM_Main <= IDLE;
        end
      end

      TX_START_BIT: begin
        o_TX_Serial <= 1'b0; //start bit = 0

        if (r_Clock_Count < CLKS_PER_BIT-1) begin
          r_Clock_Count <= r_Clock_Count + 1;
          r_SM_Main     <= TX_START_BIT;
        end else begin
          r_Clock_Count <= 0;
          r_SM_Main     <= TX_DATA_BITS;
        end
      end

      TX_DATA_BITS: begin
        o_TX_Serial <= r_TX_Data[r_Bit_Index]; //LSB first

        if (r_Clock_Count < CLKS_PER_BIT-1) begin
          r_Clock_Count <= r_Clock_Count + 1;
          r_SM_Main     <= TX_DATA_BITS;
        end else begin
          r_Clock_Count <= 0;

          if (r_Bit_Index < 7) begin
            r_Bit_Index <= r_Bit_Index + 1;
            r_SM_Main   <= TX_DATA_BITS;
          end else begin
            r_Bit_Index <= 0;
            r_SM_Main   <= TX_STOP_BIT;
          end
        end
      end

      TX_STOP_BIT: begin
        o_TX_Serial <= 1'b1; //stop bit = 1

        if (r_Clock_Count < CLKS_PER_BIT-1) begin
          r_Clock_Count <= r_Clock_Count + 1;
          r_SM_Main     <= TX_STOP_BIT;
        end else begin
          r_Clock_Count <= 0;
          r_TX_Done     <= 1'b1;
          r_SM_Main     <= CLEANUP;
        end
      end

      CLEANUP: begin
        r_TX_Active <= 1'b0;
        r_SM_Main   <= IDLE;
      end

      default: r_SM_Main <= IDLE;

    endcase
  end

endmodule

